BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> d9e8617e240d

CREATE TABLE auth_attempts (
    key VARCHAR(64) NOT NULL, 
    bucket INTEGER NOT NULL, 
    count INTEGER NOT NULL, 
    PRIMARY KEY (key, bucket)
);

CREATE TABLE skills (
    id VARCHAR(36) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    category VARCHAR(100) NOT NULL, 
    parent_id VARCHAR(36), 
    PRIMARY KEY (id), 
    CONSTRAINT skill_not_own_parent CHECK (parent_id IS NULL OR parent_id <> id), 
    FOREIGN KEY(parent_id) REFERENCES skills (id), 
    UNIQUE (name)
);

CREATE TABLE users (
    id VARCHAR(36) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    email VARCHAR(254) NOT NULL, 
    password_hash VARCHAR(255) NOT NULL, 
    city VARCHAR(100), 
    campus VARCHAR(100), 
    bio VARCHAR(1000) NOT NULL, 
    active BOOLEAN NOT NULL, 
    is_admin BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (email)
);

CREATE TABLE admin_audit (
    id VARCHAR(36) NOT NULL, 
    admin_id VARCHAR(36) NOT NULL, 
    action VARCHAR(100) NOT NULL, 
    resource_id VARCHAR(36) NOT NULL, 
    details JSON NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(admin_id) REFERENCES users (id)
);

CREATE TABLE availability (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    mode VARCHAR(10) NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT availability_mode CHECK (mode IN ('ONLINE','IN_PERSON')), 
    CONSTRAINT positive_availability CHECK (ends_at > starts_at), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_availability_user_time ON availability (user_id, starts_at, ends_at);

CREATE TABLE blocks (
    user_id VARCHAR(36) NOT NULL, 
    blocked_id VARCHAR(36) NOT NULL, 
    PRIMARY KEY (user_id, blocked_id), 
    CONSTRAINT cannot_block_self CHECK (user_id <> blocked_id), 
    FOREIGN KEY(blocked_id) REFERENCES users (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE notifications (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    content VARCHAR(500) NOT NULL, 
    resource_id VARCHAR(36), 
    is_read BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_notifications_user_created ON notifications (user_id, created_at);

CREATE TABLE requests (
    id VARCHAR(36) NOT NULL, 
    learner_id VARCHAR(36) NOT NULL, 
    provider_id VARCHAR(36), 
    skill_id VARCHAR(36) NOT NULL, 
    offered_skill_id VARCHAR(36), 
    duration_minutes INTEGER NOT NULL, 
    window_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    window_end TIMESTAMP WITH TIME ZONE NOT NULL, 
    selected_start TIMESTAMP WITH TIME ZONE, 
    mode VARCHAR(10) NOT NULL, 
    status VARCHAR(12) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT request_mode CHECK (mode IN ('ONLINE','IN_PERSON')), 
    CONSTRAINT request_status CHECK (status IN ('OPEN','REQUESTED','ACCEPTED','REJECTED','CANCELLED','FULFILLED')), 
    CONSTRAINT request_duration CHECK (duration_minutes BETWEEN 1 AND 480), 
    CONSTRAINT request_not_self CHECK (provider_id IS NULL OR provider_id <> learner_id), 
    CONSTRAINT request_window CHECK (window_end > window_start), 
    FOREIGN KEY(learner_id) REFERENCES users (id), 
    FOREIGN KEY(offered_skill_id) REFERENCES skills (id), 
    FOREIGN KEY(provider_id) REFERENCES users (id), 
    FOREIGN KEY(skill_id) REFERENCES skills (id)
);

CREATE INDEX ix_requests_learner_created ON requests (learner_id, created_at);

CREATE INDEX ix_requests_provider_created ON requests (provider_id, created_at);

CREATE TABLE user_skills (
    user_id VARCHAR(36) NOT NULL, 
    skill_id VARCHAR(36) NOT NULL, 
    kind VARCHAR(5) NOT NULL, 
    level INTEGER NOT NULL, 
    PRIMARY KEY (user_id, skill_id, kind), 
    CONSTRAINT valid_skill_kind CHECK (kind IN ('OFFER','WANT')), 
    CONSTRAINT valid_skill_level CHECK (level BETWEEN 1 AND 5), 
    FOREIGN KEY(skill_id) REFERENCES skills (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_user_skills_lookup ON user_skills (skill_id, kind);

CREATE TABLE match_runs (
    id VARCHAR(36) NOT NULL, 
    request_id VARCHAR(36) NOT NULL, 
    algorithm VARCHAR(30) NOT NULL, 
    weights JSON NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(request_id) REFERENCES requests (id)
);

CREATE INDEX ix_match_runs_request_id ON match_runs (request_id);

CREATE TABLE sessions (
    id VARCHAR(36) NOT NULL, 
    request_id VARCHAR(36) NOT NULL, 
    learner_id VARCHAR(36) NOT NULL, 
    provider_id VARCHAR(36) NOT NULL, 
    skill_id VARCHAR(36) NOT NULL, 
    starts_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    ends_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    status VARCHAR(12) NOT NULL, 
    actual_minutes INTEGER, 
    completed_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    CONSTRAINT session_status CHECK (status IN ('SCHEDULED','IN_PROGRESS','COMPLETED','CANCELLED','DISPUTED','REVERSED')), 
    CONSTRAINT session_actual CHECK (actual_minutes IS NULL OR actual_minutes BETWEEN 1 AND 480), 
    CONSTRAINT session_interval CHECK (ends_at > starts_at), 
    CONSTRAINT session_not_self CHECK (learner_id <> provider_id), 
    FOREIGN KEY(learner_id) REFERENCES users (id), 
    FOREIGN KEY(provider_id) REFERENCES users (id), 
    FOREIGN KEY(request_id) REFERENCES requests (id), 
    FOREIGN KEY(skill_id) REFERENCES skills (id), 
    UNIQUE (request_id)
);

CREATE INDEX ix_sessions_learner_time ON sessions (learner_id, starts_at, ends_at);

CREATE INDEX ix_sessions_provider_time ON sessions (provider_id, starts_at, ends_at);

CREATE TABLE confirmations (
    session_id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    minutes INTEGER NOT NULL, 
    PRIMARY KEY (session_id, user_id), 
    CONSTRAINT confirmation_minutes CHECK (minutes BETWEEN 1 AND 480), 
    FOREIGN KEY(session_id) REFERENCES sessions (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE credit_ledger (
    id VARCHAR(36) NOT NULL, 
    sender_id VARCHAR(36), 
    receiver_id VARCHAR(36) NOT NULL, 
    session_id VARCHAR(36), 
    reversal_of VARCHAR(36), 
    kind VARCHAR(10) NOT NULL, 
    minutes INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT credit_shape CHECK ((kind='GRANT' AND sender_id IS NULL AND session_id IS NULL AND reversal_of IS NULL) OR (kind='TRANSFER' AND sender_id IS NOT NULL AND session_id IS NOT NULL AND reversal_of IS NULL) OR (kind='REVERSAL' AND sender_id IS NOT NULL AND session_id IS NOT NULL AND reversal_of IS NOT NULL)), 
    CONSTRAINT credit_kind CHECK (kind IN ('GRANT','TRANSFER','REVERSAL')), 
    CONSTRAINT credit_positive CHECK (minutes > 0), 
    CONSTRAINT credit_not_self CHECK (sender_id IS NULL OR sender_id <> receiver_id), 
    FOREIGN KEY(receiver_id) REFERENCES users (id), 
    FOREIGN KEY(reversal_of) REFERENCES credit_ledger (id), 
    FOREIGN KEY(sender_id) REFERENCES users (id), 
    FOREIGN KEY(session_id) REFERENCES sessions (id), 
    UNIQUE (reversal_of)
);

CREATE INDEX ix_credit_receiver ON credit_ledger (receiver_id);

CREATE INDEX ix_credit_sender ON credit_ledger (sender_id);

CREATE UNIQUE INDEX unique_session_credit_kind ON credit_ledger (session_id, kind) WHERE session_id IS NOT NULL;

CREATE UNIQUE INDEX unique_starter_grant ON credit_ledger (receiver_id) WHERE kind = 'GRANT';

CREATE TABLE disputes (
    id VARCHAR(36) NOT NULL, 
    session_id VARCHAR(36) NOT NULL, 
    reporter_id VARCHAR(36) NOT NULL, 
    reason VARCHAR(2000) NOT NULL, 
    previous_status VARCHAR(12) NOT NULL, 
    status VARCHAR(10) NOT NULL, 
    resolution VARCHAR(2000), 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT dispute_status CHECK (status IN ('OPEN','RESOLVED')), 
    FOREIGN KEY(reporter_id) REFERENCES users (id), 
    FOREIGN KEY(session_id) REFERENCES sessions (id), 
    UNIQUE (session_id)
);

CREATE TABLE match_candidates (
    id VARCHAR(36) NOT NULL, 
    run_id VARCHAR(36) NOT NULL, 
    provider_id VARCHAR(36) NOT NULL, 
    offered_skill_id VARCHAR(36) NOT NULL, 
    score DOUBLE PRECISION NOT NULL, 
    factors JSON NOT NULL, 
    suggested_start TIMESTAMP WITH TIME ZONE NOT NULL, 
    hierarchy_distance INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(offered_skill_id) REFERENCES skills (id), 
    FOREIGN KEY(provider_id) REFERENCES users (id), 
    FOREIGN KEY(run_id) REFERENCES match_runs (id), 
    CONSTRAINT unique_run_provider UNIQUE (run_id, provider_id)
);

CREATE TABLE reputation_events (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    skill_id VARCHAR(36), 
    session_id VARCHAR(36) NOT NULL, 
    source_key VARCHAR(100) NOT NULL, 
    delta INTEGER NOT NULL, 
    kind VARCHAR(30) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(session_id) REFERENCES sessions (id), 
    FOREIGN KEY(skill_id) REFERENCES skills (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    CONSTRAINT unique_reputation_event UNIQUE (user_id, source_key)
);

CREATE INDEX ix_reputation_user_skill_time ON reputation_events (user_id, skill_id, created_at);

CREATE TABLE reservations (
    session_id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    minutes INTEGER NOT NULL, 
    status VARCHAR(10) NOT NULL, 
    PRIMARY KEY (session_id), 
    CONSTRAINT reservation_status CHECK (status IN ('HELD','RELEASED','CONSUMED')), 
    CONSTRAINT reservation_positive CHECK (minutes > 0), 
    FOREIGN KEY(session_id) REFERENCES sessions (id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE INDEX ix_reservations_user_status ON reservations (user_id, status);

CREATE TABLE reviews (
    id VARCHAR(36) NOT NULL, 
    session_id VARCHAR(36) NOT NULL, 
    reviewer_id VARCHAR(36) NOT NULL, 
    reviewee_id VARCHAR(36) NOT NULL, 
    stars INTEGER NOT NULL, 
    comment VARCHAR(2000) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CONSTRAINT review_not_self CHECK (reviewer_id <> reviewee_id), 
    CONSTRAINT review_stars CHECK (stars BETWEEN 1 AND 5), 
    FOREIGN KEY(reviewee_id) REFERENCES users (id), 
    FOREIGN KEY(reviewer_id) REFERENCES users (id), 
    FOREIGN KEY(session_id) REFERENCES sessions (id), 
    CONSTRAINT unique_participant_review UNIQUE (session_id, reviewer_id)
);

CREATE INDEX ix_reviews_reviewee_id ON reviews (reviewee_id);

INSERT INTO alembic_version (version_num) VALUES ('d9e8617e240d') RETURNING alembic_version.version_num;

-- Running upgrade d9e8617e240d -> 002_integrity

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
    DECLARE balance bigint; holds bigint; s sessions%%ROWTYPE; original credit_ledger%%ROWTYPE;
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
    DECLARE balance bigint; holds bigint; s sessions%%ROWTYPE; duration integer;
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
    DECLARE s sessions%%ROWTYPE; held integer;
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
    CREATE TRIGGER confirmation_participant_guard BEFORE INSERT OR UPDATE ON confirmations FOR EACH ROW EXECUTE FUNCTION validate_session_participant();;

UPDATE alembic_version SET version_num='002_integrity' WHERE alembic_version.version_num = 'd9e8617e240d';

COMMIT;

