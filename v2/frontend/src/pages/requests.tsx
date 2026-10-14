import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { allPages, post } from "../api/client";
import { Page, RequestItem, Schema, SessionItem } from "../api/types";
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

export function RequestList() {
  const auth = useAuth(),
    [offset, setOffset] = useState(0),
    [view, setView] = useState("all"),
    limit = 20;
  const requests = useData<Page<RequestItem>>(
    ["requests", offset, view],
    "/requests?limit=" + limit + "&offset=" + offset + "&role=" + view,
    true,
    10000,
  );
  const rows = requests.data?.items;
  return (
    <div className="container app-page">
      <h1>Your session requests</h1>
      <ActivityNav />
      <Field label="Show requests">
        <select
          value={view}
          onChange={(e) => {
            setView(e.target.value);
            setOffset(0);
          }}
        >
          <option value="all">Teaching and learning</option>
          <option value="teaching">Incoming teaching requests</option>
          <option value="learning">My learning requests</option>
        </select>
      </Field>
      {requests.isPending ? (
        <Loading />
      ) : requests.error ? (
        <ErrorNotice error={requests.error} retry={requests.refetch} />
      ) : rows?.length ? (
        <section className="panel">
          <ul className="list">
            {rows.map((r) => (
              <li key={r.id}>
                <div className="row">
                  <div>
                    <Link to={"/requests/" + r.id}>
                      <strong>
                        <SkillName id={r.skill_id} />
                      </strong>
                    </Link>
                    <p>
                      {minutes(r.duration_minutes)} ·{" "}
                      {r.mode === "ONLINE" ? "Online" : "In person"}
                    </p>
                    <small>
                      {r.provider_id === auth.me?.id
                        ? "Teaching request from "
                        : "Learning request with "}
                      {r.provider_id === auth.me?.id ? (
                        <MemberName id={r.learner_id} />
                      ) : r.provider_id ? (
                        <MemberName id={r.provider_id} />
                      ) : (
                        "No member selected"
                      )}
                    </small>
                  </div>
                  <Status value={r.status} />
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <Empty title="No requests on this page">
          <Link to="/explore">Find a learning partner</Link>
        </Empty>
      )}
      <Pagination
        offset={offset}
        count={requests.data?.items.length || 0}
        limit={limit}
        onChange={setOffset}
      />
    </div>
  );
}

export function RequestDetails() {
  const { id } = useParams(),
    auth = useAuth(),
    task = useTask(),
    navigate = useNavigate();
  const request = useData<RequestItem>(
    ["request", id],
    "/requests/" + id,
    true,
    5000,
  );
  const sessions = useQuery({
    queryKey: ["all-sessions"],
    queryFn: ({ signal }) => allPages<SessionItem>("/sessions", signal),
    enabled:
      request.data?.status === "ACCEPTED" ||
      request.data?.status === "FULFILLED",
  });
  const [matches, setMatches] = useState<Schema["MatchResults"] | null>(null);
  if (request.isPending)
    return (
      <div className="container">
        <Loading />
      </div>
    );
  if (request.error)
    return (
      <div className="container">
        <ErrorNotice error={request.error} />
      </div>
    );
  const r = request.data!,
    teaching = r.provider_id === auth.me?.id,
    session = sessions.data?.find((s) => s.request_id === r.id);
  return (
    <div className="container app-page">
      <Link to="/requests" className="back-link">
        Back to requests
      </Link>
      <div className="page-heading">
        <div>
          <h1>
            <SkillName id={r.skill_id} />
          </h1>
          <p>
            {teaching
              ? "An incoming teaching request"
              : "Your learning request"}
          </p>
        </div>
        <Status value={r.status} />
      </div>
      <section className="panel">
        <dl className="details-grid">
          <div>
            <dt>Duration</dt>
            <dd>{minutes(r.duration_minutes)}</dd>
          </div>
          <div>
            <dt>Mode</dt>
            <dd>{r.mode === "ONLINE" ? "Online" : "In person"}</dd>
          </div>
          <div>
            <dt>Requested window</dt>
            <dd>
              {localTime(r.window_start)} — {localTime(r.window_end)}
            </dd>
          </div>
          <div>
            <dt>Suggested start</dt>
            <dd>
              {r.selected_start
                ? localTime(r.selected_start)
                : "Choose a matching member"}
            </dd>
          </div>
          <div>
            <dt>Learner</dt>
            <dd>
              <MemberName id={r.learner_id} />
            </dd>
          </div>
          <div>
            <dt>Teacher</dt>
            <dd>
              {r.provider_id ? (
                <MemberName id={r.provider_id} />
              ) : (
                "Not selected yet"
              )}
            </dd>
          </div>
        </dl>
        <small>
          Times shown in {timezone}. Credits are reserved when the teacher
          accepts.
        </small>
        <Feedback task={task} />
        <div className="actions">
          {teaching && r.status === "REQUESTED" && (
            <>
              <button
                className="button"
                disabled={task.busy}
                onClick={async () => {
                  const result = await task.run(
                    () => post<SessionItem>("/requests/" + id + "/accept"),
                    "Request accepted.",
                  );
                  if (result) navigate("/sessions/" + result.value.id);
                }}
              >
                Accept request
              </button>
              <button
                className="button secondary"
                disabled={task.busy}
                onClick={() =>
                  task.run(
                    () => post("/requests/" + id + "/reject"),
                    "Request rejected.",
                  )
                }
              >
                Reject request
              </button>
            </>
          )}
          {r.learner_id === auth.me?.id &&
            ["OPEN", "REQUESTED"].includes(r.status) && (
              <button
                className="button secondary"
                disabled={task.busy}
                onClick={() =>
                  task.run(
                    () => post("/requests/" + id + "/cancel"),
                    "Request cancelled.",
                  )
                }
              >
                Cancel request
              </button>
            )}
          {r.learner_id === auth.me?.id && r.status === "OPEN" && (
            <button
              className="button"
              disabled={task.busy}
              onClick={async () => {
                const result = await task.run(
                  () =>
                    post<Schema["MatchResults"]>(
                      "/requests/" + id + "/matches",
                    ),
                  "Matches refreshed.",
                );
                if (result) setMatches(result.value);
              }}
            >
              Find matching members
            </button>
          )}
          {session && (
            <Link className="button" to={"/sessions/" + session.id}>
              Open scheduled session
            </Link>
          )}
        </div>
        {sessions.error && <ErrorNotice error={sessions.error} />}
      </section>
      {matches && r.status === "OPEN" && (
        <section className="panel admin-section">
          <h2>Available matches</h2>
          {matches.candidates.length ? (
            <ul className="list">
              {matches.candidates.map((c) => (
                <li key={c.id}>
                  <div className="row">
                    <div>
                      <strong>
                        <MemberName id={c.provider_id} />
                      </strong>
                      <p>{localTime(c.suggested_start)}</p>
                      <small>
                        {c.hierarchy_distance
                          ? "Related parent skill match"
                          : "Exact skill match"}
                      </small>
                    </div>
                    <button
                      className="button secondary"
                      disabled={task.busy}
                      onClick={() =>
                        task.run(
                          () =>
                            post("/requests/" + id + "/select", {
                              candidate_id: c.id,
                            }),
                          "Request sent to this member.",
                        )
                      }
                    >
                      Request this member
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p>No eligible members have a free slot in this window.</p>
          )}
        </section>
      )}
    </div>
  );
}
