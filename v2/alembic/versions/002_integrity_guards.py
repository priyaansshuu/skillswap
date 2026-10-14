"""Protect the ledger and validate accounting at the database boundary."""

from alembic import op

revision = "002_integrity"
down_revision = "d9e8617e240d"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    CREATE FUNCTION reject_immutable_change() RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN RAISE EXCEPTION 'Immutable record: use a linked correction' USING ERRCODE='23514'; END $$;
    CREATE TRIGGER ledger_immutable BEFORE UPDATE OR DELETE ON credit_ledger
      FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
    CREATE TRIGGER audit_immutable BEFORE UPDATE OR DELETE ON admin_audit
      FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
    CREATE TRIGGER reputation_immutable BEFORE UPDATE OR DELETE ON reputation_events
      FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();
    CREATE TRIGGER review_immutable BEFORE UPDATE OR DELETE ON reviews
      FOR EACH ROW EXECUTE FUNCTION reject_immutable_change();

    CREATE FUNCTION validate_credit_insert() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE balance bigint; holds bigint; s sessions%ROWTYPE; original credit_ledger%ROWTYPE;
    BEGIN
      PERFORM id FROM users WHERE id IN (NEW.sender_id, NEW.receiver_id) ORDER BY id FOR UPDATE;
      IF NEW.kind <> 'GRANT' THEN
        SELECT * INTO s FROM sessions WHERE id=NEW.session_id;
        IF NEW.kind='TRANSFER' THEN
          IF s.status<>'COMPLETED' OR NEW.sender_id<>s.learner_id OR NEW.receiver_id<>s.provider_id
             OR NEW.minutes IS DISTINCT FROM s.actual_minutes THEN
            RAISE EXCEPTION 'Invalid session transfer' USING ERRCODE='23514';
          END IF;
        ELSE
          SELECT * INTO original FROM credit_ledger WHERE id=NEW.reversal_of;
          IF original.kind<>'TRANSFER' OR NEW.sender_id<>original.receiver_id OR NEW.receiver_id<>original.sender_id
             OR NEW.minutes<>original.minutes OR NEW.session_id<>original.session_id OR s.status<>'REVERSED' THEN
            RAISE EXCEPTION 'Invalid linked reversal' USING ERRCODE='23514';
          END IF;
        END IF;
        SELECT COALESCE(SUM(CASE WHEN receiver_id=NEW.sender_id THEN minutes ELSE -minutes END),0)
          INTO balance FROM credit_ledger WHERE receiver_id=NEW.sender_id OR sender_id=NEW.sender_id;
        SELECT COALESCE(SUM(minutes),0) INTO holds FROM reservations WHERE user_id=NEW.sender_id AND status='HELD';
        IF balance-NEW.minutes < holds THEN
          RAISE EXCEPTION 'Credit transfer would spend reserved or unavailable credits' USING ERRCODE='23514';
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER validate_credit BEFORE INSERT ON credit_ledger FOR EACH ROW EXECUTE FUNCTION validate_credit_insert();

    CREATE FUNCTION validate_reservation() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE balance bigint; holds bigint; s sessions%ROWTYPE; duration integer;
    BEGIN
      PERFORM id FROM users WHERE id=NEW.user_id FOR UPDATE;
      SELECT * INTO s FROM sessions WHERE id=NEW.session_id;
      SELECT duration_minutes INTO duration FROM requests WHERE id=s.request_id;
      IF NEW.user_id<>s.learner_id OR NEW.minutes<>duration THEN
        RAISE EXCEPTION 'Invalid session reservation' USING ERRCODE='23514';
      END IF;
      IF TG_OP='UPDATE' AND (NEW.user_id<>OLD.user_id OR NEW.session_id<>OLD.session_id OR NEW.minutes<>OLD.minutes
          OR (OLD.status<>'HELD' AND NEW.status<>OLD.status)) THEN
        RAISE EXCEPTION 'Reservation cannot be reassigned or reused' USING ERRCODE='23514';
      END IF;
      IF NEW.status='HELD' THEN
        SELECT COALESCE(SUM(CASE WHEN receiver_id=NEW.user_id THEN minutes ELSE -minutes END),0)
          INTO balance FROM credit_ledger WHERE receiver_id=NEW.user_id OR sender_id=NEW.user_id;
        SELECT COALESCE(SUM(minutes),0) INTO holds FROM reservations
          WHERE user_id=NEW.user_id AND status='HELD' AND session_id<>NEW.session_id;
        IF balance < holds+NEW.minutes THEN
          RAISE EXCEPTION 'Insufficient credits for reservation' USING ERRCODE='23514';
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER reservation_guard BEFORE INSERT OR UPDATE ON reservations FOR EACH ROW EXECUTE FUNCTION validate_reservation();

    CREATE FUNCTION validate_session_participant() RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE s sessions%ROWTYPE; held integer;
    BEGIN
      SELECT * INTO s FROM sessions WHERE id=NEW.session_id;
      IF TG_TABLE_NAME='reviews' THEN
        IF s.status<>'COMPLETED' OR NEW.reviewer_id NOT IN (s.learner_id,s.provider_id)
           OR NEW.reviewee_id NOT IN (s.learner_id,s.provider_id) OR NEW.reviewer_id=NEW.reviewee_id THEN
          RAISE EXCEPTION 'Only completed-session participants can review' USING ERRCODE='23514';
        END IF;
      ELSE
        SELECT minutes INTO held FROM reservations WHERE session_id=s.id;
        IF s.status<>'IN_PROGRESS' OR NEW.user_id NOT IN (s.learner_id,s.provider_id) OR NEW.minutes>held THEN
          RAISE EXCEPTION 'Invalid completion confirmation' USING ERRCODE='23514';
        END IF;
      END IF;
      RETURN NEW;
    END $$;
    CREATE TRIGGER review_participant_guard BEFORE INSERT ON reviews FOR EACH ROW EXECUTE FUNCTION validate_session_participant();
    CREATE TRIGGER confirmation_participant_guard BEFORE INSERT OR UPDATE ON confirmations FOR EACH ROW EXECUTE FUNCTION validate_session_participant();
    """)


def downgrade():
    for table, trigger in [
        ("credit_ledger", "ledger_immutable"),
        ("admin_audit", "audit_immutable"),
        ("reputation_events", "reputation_immutable"),
        ("reviews", "review_immutable"),
        ("credit_ledger", "validate_credit"),
        ("reservations", "reservation_guard"),
        ("reviews", "review_participant_guard"),
        ("confirmations", "confirmation_participant_guard"),
    ]:
        op.execute(f"DROP TRIGGER {trigger} ON {table}")
    for function in [
        "reject_immutable_change",
        "validate_credit_insert",
        "validate_reservation",
        "validate_session_participant",
    ]:
        op.execute(f"DROP FUNCTION {function}()")
