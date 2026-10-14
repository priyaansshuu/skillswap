import { useEffect, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { post } from "../api/client";
import { Page, Schema, SessionItem } from "../api/types";
import { useAuth } from "../auth-context";
import {
  Empty,
  ErrorNotice,
  Feedback,
  Field,
  Loading,
  localTime,
  minutes,
  Pagination,
  Status,
  timezone,
  useData,
  useTask,
} from "../components/ui";
import { ActivityNav, MemberName, SkillName } from "./activity-shared";

export function SessionList() {
  const auth = useAuth(),
    [offset, setOffset] = useState(0),
    limit = 20;
  const sessions = useData<Page<SessionItem>>(
    ["sessions", offset],
    "/sessions?limit=" + limit + "&offset=" + offset,
    true,
    10000,
  );
  return (
    <div className="container app-page">
      <h1>Your shared time</h1>
      <ActivityNav />
      {sessions.isPending ? (
        <Loading />
      ) : sessions.error ? (
        <ErrorNotice error={sessions.error} retry={sessions.refetch} />
      ) : sessions.data?.items.length ? (
        <section className="panel">
          <ul className="list">
            {sessions.data.items.map((s) => (
              <li key={s.id}>
                <div className="row">
                  <div>
                    <Link to={"/sessions/" + s.id}>
                      <strong>
                        <SkillName id={s.skill_id} />
                      </strong>
                    </Link>
                    <p>
                      {localTime(s.starts_at)} — {localTime(s.ends_at)}
                    </p>
                    <small>
                      {auth.me?.id === s.provider_id ? "Teaching" : "Learning"}{" "}
                      with{" "}
                      <MemberName
                        id={
                          auth.me?.id === s.provider_id
                            ? s.learner_id
                            : s.provider_id
                        }
                      />
                    </small>
                  </div>
                  <Status value={s.status} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <Empty title="No sessions scheduled">
          <Link to="/explore">Find a skill to learn</Link>
        </Empty>
      )}
      <Pagination
        offset={offset}
        count={sessions.data?.items.length || 0}
        limit={limit}
        onChange={setOffset}
      />
    </div>
  );
}

export function SessionDetails() {
  const { id } = useParams(),
    auth = useAuth(),
    task = useTask();
  const session = useData<SessionItem>(
    ["session", id],
    "/sessions/" + id,
    true,
    5000,
  );
  const confirmations = useData<Schema["ConfirmationOut"][]>(
    ["confirmations", id],
    "/sessions/" + id + "/confirmations",
    true,
    5000,
  );
  const reviews = useData<Schema["ReviewOut"][]>(
    ["reviews", id],
    "/sessions/" + id + "/reviews",
    true,
    10000,
  );
  const dispute = useData<Schema["DisputeOut"]>(
    ["dispute", id],
    "/sessions/" + id + "/dispute",
    session.data?.status === "DISPUTED",
  );
  const [now, setNow] = useState(Date.now()),
    [duration, setDuration] = useState(1),
    [reviewOpen, setReviewOpen] = useState(false),
    [disputeOpen, setDisputeOpen] = useState(false);
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    if (session.data)
      setDuration(
        Math.round(
          (new Date(session.data.ends_at).getTime() -
            new Date(session.data.starts_at).getTime()) /
            60000,
        ),
      );
  }, [session.data?.starts_at, session.data?.ends_at]);
  async function review(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const result = await task.run(
      () =>
        post("/sessions/" + id + "/reviews", {
          stars: Number(data.get("stars")),
          comment: String(data.get("comment")),
        }),
      "Review added.",
    );
    if (result) setReviewOpen(false);
  }
  async function report(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const result = await task.run(
      () =>
        post("/sessions/" + id + "/disputes", {
          reason: String(data.get("reason")),
        }),
      "Dispute sent to an administrator.",
    );
    if (result) setDisputeOpen(false);
  }
  if (session.isPending)
    return (
      <div className="container">
        <Loading />
      </div>
    );
  if (session.error)
    return (
      <div className="container">
        <ErrorNotice error={session.error} />
      </div>
    );
  const s = session.data!,
    start = new Date(s.starts_at).getTime(),
    end = new Date(s.ends_at).getTime(),
    reserved = Math.round((end - start) / 60000);
  const own = confirmations.data?.find((c) => c.user_id === auth.me?.id),
    other = confirmations.data?.find((c) => c.user_id !== auth.me?.id);
  return (
    <div className="container app-page">
      <Link to="/sessions" className="back-link">
        Back to sessions
      </Link>
      <div className="page-heading">
        <div>
          <h1>
            <SkillName id={s.skill_id} />
          </h1>
          <p>
            {s.provider_id === auth.me?.id
              ? "You are teaching"
              : "You are learning"}{" "}
            with{" "}
            <MemberName
              id={s.provider_id === auth.me?.id ? s.learner_id : s.provider_id}
            />
          </p>
        </div>
        <Status value={s.status} />
      </div>
      <section className="panel">
        <dl className="details-grid">
          <div>
            <dt>Starts</dt>
            <dd>{localTime(s.starts_at)}</dd>
          </div>
          <div>
            <dt>Ends</dt>
            <dd>{localTime(s.ends_at)}</dd>
          </div>
          <div>
            <dt>Reserved duration</dt>
            <dd>{minutes(reserved)}</dd>
          </div>
          <div>
            <dt>Confirmed duration</dt>
            <dd>
              {s.actual_minutes
                ? minutes(s.actual_minutes)
                : "Waiting for both participants"}
            </dd>
          </div>
        </dl>
        <small>
          Timezone: {timezone}. Sessions happen outside SkillSwap; use this page
          to track their status.
        </small>
        <Feedback task={task} />
        {s.status === "SCHEDULED" && (
          <>
            <p className="hint">
              {now < start
                ? "The start button becomes available at the scheduled time."
                : "Your scheduled start has arrived."}
            </p>
            <div className="actions">
              <button
                className="button"
                disabled={task.busy || now < start}
                onClick={() =>
                  task.run(
                    () => post("/sessions/" + id + "/start"),
                    "Session started.",
                  )
                }
              >
                Start session
              </button>
              {now < start && (
                <button
                  className="button secondary"
                  disabled={task.busy}
                  onClick={() =>
                    task.run(
                      () => post("/sessions/" + id + "/cancel"),
                      "Session cancelled; reserved credits released.",
                    )
                  }
                >
                  Cancel session
                </button>
              )}
            </div>
          </>
        )}
        {s.status === "IN_PROGRESS" && (
          <>
            <h2 className="admin-section">Confirm completed time</h2>
            <p>
              {now < end
                ? "Completion opens after the scheduled end."
                : "Both participants must confirm the same duration before credits transfer."}
            </p>
            <div className="confirmation-list">
              <p>You: {own ? minutes(own.minutes) : "Not confirmed"}</p>
              <p>
                Your partner: {other ? minutes(other.minutes) : "Not confirmed"}
              </p>
            </div>
            {own && other && own.minutes !== other.minutes && (
              <div className="notice error" role="status">
                Your durations differ. Agree on the completed time, then update
                your confirmation. No credits have transferred.
              </div>
            )}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                void task.run(
                  () =>
                    post("/sessions/" + id + "/confirm", { minutes: duration }),
                  "Your duration is confirmed.",
                );
              }}
            >
              <Field
                label="Actual minutes completed"
                hint={
                  "Maximum " +
                  reserved +
                  " minutes, up to the reserved duration."
                }
              >
                <input
                  type="number"
                  min={1}
                  max={reserved}
                  required
                  value={duration}
                  onChange={(e) => setDuration(Number(e.target.value))}
                />
              </Field>
              <button className="button" disabled={task.busy || now < end}>
                {own ? "Update my confirmation" : "Confirm completion"}
              </button>
            </form>
          </>
        )}
        {confirmations.error && <ErrorNotice error={confirmations.error} />}{" "}
        {s.status === "COMPLETED" && (
          <p className="success">
            {confirmations.data?.length === 2 &&
            confirmations.data.every((c) => c.minutes === s.actual_minutes)
              ? "Both participants confirmed."
              : "Recorded completed session."}{" "}
            {minutes(s.actual_minutes || 0)} transferred exactly once.
          </p>
        )}
        {["SCHEDULED", "IN_PROGRESS", "COMPLETED", "CANCELLED"].includes(
          s.status,
        ) && (
          <button
            className="text-button"
            onClick={() => setDisputeOpen(!disputeOpen)}
          >
            Report a problem
          </button>
        )}
        {disputeOpen && (
          <form onSubmit={report}>
            <Field label="Describe the problem">
              <textarea
                name="reason"
                minLength={10}
                maxLength={2000}
                required
              />
            </Field>
            <button className="button secondary" disabled={task.busy}>
              Submit dispute
            </button>
          </form>
        )}
        {s.status === "DISPUTED" && (
          <div className="notice">
            <div>
              <h2>Awaiting administrator review</h2>
              <p>Completion is paused while this dispute is reviewed.</p>
              {dispute.data && <p>{dispute.data.reason}</p>}
              {dispute.error && <ErrorNotice error={dispute.error} />}
            </div>
          </div>
        )}
      </section>
      <section className="panel admin-section">
        <h2>Session reviews</h2>
        {reviews.isPending ? (
          <Loading />
        ) : reviews.error ? (
          <ErrorNotice error={reviews.error} />
        ) : reviews.data?.length ? (
          <ul className="list">
            {reviews.data.map((r) => (
              <li key={r.id}>
                <strong>
                  {r.stars} / 5 ·{" "}
                  {r.reviewer_id === auth.me?.id
                    ? "Your review"
                    : "Your partner’s review"}
                </strong>
                <p>{r.comment || "No written comment."}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p>No reviews yet.</p>
        )}
        {s.status === "COMPLETED" &&
          !reviews.data?.some((r) => r.reviewer_id === auth.me?.id) && (
            <button
              className="button secondary"
              onClick={() => setReviewOpen(!reviewOpen)}
            >
              Write a review
            </button>
          )}
        {reviewOpen && (
          <form onSubmit={review}>
            <Field label="Rating">
              <select name="stars" defaultValue="5">
                {[5, 4, 3, 2, 1].map((n) => (
                  <option key={n} value={n}>
                    {n} of 5
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Your review">
              <textarea name="comment" maxLength={2000} />
            </Field>
            <button className="button" disabled={task.busy}>
              Post review
            </button>
          </form>
        )}
      </section>
    </div>
  );
}
