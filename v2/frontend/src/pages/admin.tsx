import { useState, type FormEvent } from "react";
import { useSearchParams } from "react-router-dom";
import { api, post, put, query } from "../api/client";
import type { Page, Schema, Skill, Suggestion } from "../api/types";
import { useCatalog } from "./discovery";
import { MemberName } from "./activity-shared";
import {
  Empty,
  ErrorNotice,
  Feedback,
  Field,
  Loading,
  localTime,
  Pagination,
  Status,
  useData,
  useTask,
} from "../components/ui";

const tabs = [
  ["skills", "Skill catalog"],
  ["suggestions", "Skill suggestions"],
  ["members", "Members"],
  ["disputes", "Disputes"],
  ["audit", "Audit history"],
  ["evaluation", "Evaluation"],
] as const;
export function Admin() {
  const [params, setParams] = useSearchParams(),
    tab = params.get("tab") || "skills";
  return (
    <div className="container app-page">
      <h1>Keep SkillSwap running well</h1>
      <p>Manage the catalog, member safety, and recorded activity.</p>
      <nav className="activity-tabs" aria-label="Administration">
        {tabs.map(([key, label]) => (
          <button
            key={key}
            className={"text-button " + (tab === key ? "active" : "")}
            onClick={() => setParams({ tab: key })}
          >
            {label}
          </button>
        ))}
      </nav>
      {tab === "skills" ? (
        <CatalogAdmin />
      ) : tab === "suggestions" ? (
        <SuggestionAdmin />
      ) : tab === "members" ? (
        <MemberAdmin />
      ) : tab === "disputes" ? (
        <DisputeAdmin />
      ) : tab === "audit" ? (
        <AuditAdmin />
      ) : tab === "evaluation" ? (
        <EvaluationAdmin />
      ) : (
        <Empty title="Choose an administration section" />
      )}
    </div>
  );
}
function CatalogAdmin() {
  const catalog = useCatalog(),
    [editing, setEditing] = useState<Skill | null>(null),
    task = useTask();
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const body = {
      name: String(data.get("name")),
      category: String(data.get("category")),
      parent_id: String(data.get("parent_id")) || null,
    };
    const response = await task.run(
      () =>
        editing ? put("/skills/" + editing.id, body) : post("/skills", body),
      "Catalog updated.",
    );
    if (response) setEditing(null);
  }
  return (
    <div className="account-grid">
      <section className="panel">
        <h2>Skill hierarchy</h2>
        {catalog.isPending ? (
          <Loading />
        ) : catalog.error ? (
          <ErrorNotice error={catalog.error} />
        ) : (
          <ul className="list">
            {catalog.data?.map((s) => (
              <li key={s.id}>
                <div className="row">
                  <div>
                    <strong>{s.name}</strong>
                    <p>{s.category}</p>
                    <small>
                      Parent:{" "}
                      {catalog.data.find((p) => p.id === s.parent_id)?.name ||
                        "Top-level skill"}
                    </small>
                  </div>
                  <button className="text-button" onClick={() => setEditing(s)}>
                    Edit
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="panel">
        <h2>{editing ? "Edit " + editing.name : "Add a catalog skill"}</h2>
        <form key={editing?.id || "new"} onSubmit={save}>
          <Field label="Skill name">
            <input
              name="name"
              defaultValue={editing?.name || ""}
              required
              maxLength={100}
            />
          </Field>
          <Field label="Category">
            <input
              name="category"
              defaultValue={editing?.category || ""}
              required
              maxLength={100}
            />
          </Field>
          <Field label="Parent skill">
            <select name="parent_id" defaultValue={editing?.parent_id || ""}>
              <option value="">Top-level skill</option>
              {catalog.data
                ?.filter((s) => s.id !== editing?.id)
                .map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
            </select>
          </Field>
          <button className="button" disabled={task.busy}>
            {editing ? "Save skill" : "Add skill"}
          </button>
          {editing && (
            <button
              className="text-button"
              type="button"
              onClick={() => setEditing(null)}
            >
              Cancel editing
            </button>
          )}
        </form>
        <Feedback task={task} />
        <p className="hint">
          Hierarchy cycles are rejected by the backend. Existing member offers
          remain linked to their skill.
        </p>
      </section>
    </div>
  );
}
function SuggestionAdmin() {
  const [offset, setOffset] = useState(0),
    limit = 20;
  const suggestions = useData<Page<Suggestion>>(
    ["admin-suggestions", offset],
    "/admin/skill-suggestions?limit=" + limit + "&offset=" + offset,
  );
  return (
    <>
      <h2>Member skill suggestions</h2>
      {suggestions.isPending ? (
        <Loading />
      ) : suggestions.error ? (
        <ErrorNotice error={suggestions.error} />
      ) : suggestions.data?.items.length ? (
        <div className="stack">
          {suggestions.data.items.map((s) => (
            <SuggestionResolution key={s.id} item={s} />
          ))}
        </div>
      ) : (
        <Empty title="No suggestions to review" />
      )}
      <Pagination
        offset={offset}
        count={suggestions.data?.items.length || 0}
        limit={limit}
        onChange={setOffset}
      />
    </>
  );
}
function SuggestionResolution({ item }: { item: Suggestion }) {
  const catalog = useCatalog(),
    task = useTask(),
    [action, setAction] = useState<"APPROVE" | "REJECT">("APPROVE"),
    [existing, setExisting] = useState("");
  async function resolve(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    await task.run(
      () =>
        post("/admin/skill-suggestions/" + item.id + "/resolve", {
          action,
          name:
            action === "APPROVE" && !existing ? String(data.get("name")) : null,
          category:
            action === "APPROVE" && !existing
              ? String(data.get("category"))
              : null,
          parent_id:
            action === "APPROVE" && !existing
              ? String(data.get("parent_id")) || null
              : null,
          skill_id: action === "APPROVE" ? existing || null : null,
          note: String(data.get("note")),
        }),
      "Suggestion resolved and member notified.",
    );
  }
  return (
    <section className="panel">
      <div className="row">
        <h3>{item.name}</h3>
        <Status value={item.status} />
      </div>
      <p>{item.explanation || "No explanation supplied."}</p>
      <small>
        Suggested by <MemberName id={item.user_id} />
      </small>
      {item.status === "PENDING" ? (
        <form onSubmit={resolve}>
          <div className="form-grid">
            <Field label="Decision">
              <select
                value={action}
                onChange={(e) =>
                  setAction(e.target.value as "APPROVE" | "REJECT")
                }
              >
                <option value="APPROVE">Approve</option>
                <option value="REJECT">Reject</option>
              </select>
            </Field>
            {action === "APPROVE" && (
              <Field label="Link to an existing skill">
                <select
                  value={existing}
                  onChange={(e) => setExisting(e.target.value)}
                >
                  <option value="">Create a catalog skill</option>
                  {catalog.data?.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name}
                    </option>
                  ))}
                </select>
              </Field>
            )}
            {action === "APPROVE" && !existing && (
              <>
                <Field label="Approved name">
                  <input
                    name="name"
                    defaultValue={item.name}
                    required
                    maxLength={100}
                  />
                </Field>
                <Field label="Approved category">
                  <input name="category" required maxLength={100} />
                </Field>
                <Field label="Approved parent skill">
                  <select name="parent_id">
                    <option value="">Top-level skill</option>
                    {catalog.data?.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </Field>
              </>
            )}
            <div className="wide">
              <Field label="Decision note">
                <textarea name="note" required minLength={5} maxLength={1000} />
              </Field>
            </div>
          </div>
          <button className="button" disabled={task.busy}>
            Resolve suggestion
          </button>
        </form>
      ) : (
        <p>{item.resolution}</p>
      )}
      <Feedback task={task} />
    </section>
  );
}
function MemberAdmin() {
  const [offset, setOffset] = useState(0),
    [q, setQ] = useState(""),
    limit = 20;
  const members = useData<Page<Schema["AdminMember"]>>(
    ["admin-members", q, offset],
    "/admin/users?" + query({ q, offset, limit }),
  );
  return (
    <>
      <h2>Members</h2>
      <Field label="Search members">
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOffset(0);
          }}
          placeholder="Name or email"
          maxLength={100}
        />
      </Field>
      {members.isPending ? (
        <Loading />
      ) : members.error ? (
        <ErrorNotice error={members.error} />
      ) : (
        <div className="stack">
          {members.data?.items.map((m) => (
            <ModerationForm key={m.id} member={m} />
          ))}
        </div>
      )}
      <Pagination
        offset={offset}
        count={members.data?.items.length || 0}
        limit={limit}
        onChange={setOffset}
      />
    </>
  );
}
function ModerationForm({ member }: { member: Schema["AdminMember"] }) {
  const task = useTask(),
    [open, setOpen] = useState(false);
  async function moderate(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const result = await task.run(
      () =>
        post("/admin/users/" + member.id + "/moderate", {
          active: !member.active,
          reason: String(data.get("reason")),
        }),
      "Member status updated.",
    );
    if (result) setOpen(false);
  }
  return (
    <section className="panel">
      <div className="row">
        <div>
          <h3>{member.name}</h3>
          <p>{member.email}</p>
          <small>
            {member.is_admin
              ? "Administrator"
              : member.active
                ? "Active member"
                : "Inactive member"}
          </small>
        </div>
        {!member.is_admin && (
          <button className="button secondary" onClick={() => setOpen(!open)}>
            {member.active ? "Deactivate member" : "Reactivate member"}
          </button>
        )}
      </div>
      {open && (
        <form onSubmit={moderate}>
          <Field label="Reason for this moderation action">
            <textarea name="reason" required minLength={10} maxLength={1000} />
          </Field>
          <label className="checkbox">
            <input type="checkbox" required />I confirm this member status
            change.
          </label>
          <button className="button" disabled={task.busy}>
            {member.active ? "Confirm deactivation" : "Confirm reactivation"}
          </button>
        </form>
      )}
      <Feedback task={task} />
    </section>
  );
}
function DisputeAdmin() {
  const [offset, setOffset] = useState(0),
    limit = 20;
  const disputes = useData<Page<Schema["DisputeOut"]>>(
    ["admin-disputes", offset],
    "/admin/disputes?limit=" + limit + "&offset=" + offset,
  );
  return (
    <>
      <h2>Session disputes</h2>
      {disputes.isPending ? (
        <Loading />
      ) : disputes.error ? (
        <ErrorNotice error={disputes.error} />
      ) : disputes.data?.items.length ? (
        <div className="stack">
          {disputes.data.items.map((d) => (
            <DisputeResolution key={d.id} item={d} />
          ))}
        </div>
      ) : (
        <Empty title="No disputes recorded" />
      )}
      <Pagination
        offset={offset}
        count={disputes.data?.items.length || 0}
        limit={limit}
        onChange={setOffset}
      />
    </>
  );
}
function DisputeResolution({ item }: { item: Schema["DisputeOut"] }) {
  const task = useTask(),
    [action, setAction] = useState<"DISMISS" | "CANCEL" | "REVERSE">("DISMISS"),
    [penalty, setPenalty] = useState("NONE");
  const session = useData<Schema["SessionOut"]>(
    ["admin-session", item.session_id],
    "/admin/sessions/" + item.session_id,
    item.status === "OPEN",
  );
  async function resolve(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    await task.run(
      () =>
        post("/admin/disputes/" + item.id + "/resolve", {
          action,
          note: String(data.get("note")),
          penalty,
          responsible_user_id:
            penalty === "NONE" ? null : String(data.get("responsible_user_id")),
        }),
      "Dispute resolved.",
    );
  }
  return (
    <section className="panel">
      <div className="row">
        <h3>Reported {localTime(item.created_at)}</h3>
        <Status value={item.status} />
      </div>
      <p>{item.reason}</p>
      <small>
        Previous session state:{" "}
        {item.previous_status.toLowerCase().replaceAll("_", " ")}
      </small>
      {item.status === "OPEN" ? (
        <form onSubmit={resolve}>
          <Field label="Resolution">
            <select
              value={action}
              onChange={(e) => setAction(e.target.value as typeof action)}
            >
              <option value="DISMISS">
                Dismiss dispute and restore previous state
              </option>
              {item.previous_status === "COMPLETED" ? (
                <option value="REVERSE">Reverse the completed transfer</option>
              ) : (
                <option value="CANCEL">Cancel and release held minutes</option>
              )}
            </select>
          </Field>
          <Field label="Verified penalty">
            <select
              value={penalty}
              onChange={(e) => setPenalty(e.target.value)}
            >
              <option value="NONE">No penalty</option>
              <option value="NO_SHOW">Verified no-show</option>
              <option value="UNJUSTIFIED_CANCELLATION">
                Verified unjustified cancellation
              </option>
            </select>
          </Field>
          {penalty !== "NONE" && (
            <Field label="Responsible participant">
              <select name="responsible_user_id" required>
                <option value="">Choose participant</option>
                {session.data && (
                  <>
                    <option value={session.data.learner_id}>Learner</option>
                    <option value={session.data.provider_id}>Teacher</option>
                  </>
                )}
              </select>
            </Field>
          )}
          <Field label="Resolution note">
            <textarea name="note" required minLength={10} maxLength={2000} />
          </Field>
          <label className="checkbox">
            <input type="checkbox" required />I confirm this resolution and any
            credit correction.
          </label>
          <button className="button" disabled={task.busy}>
            Resolve dispute
          </button>
          {session.error && <ErrorNotice error={session.error} />}
        </form>
      ) : (
        <p>{item.resolution}</p>
      )}
      <Feedback task={task} />
      <p className="hint">
        A reversal requires enough unreserved minutes in the teacher’s wallet.
      </p>
    </section>
  );
}
function AuditAdmin() {
  const [offset, setOffset] = useState(0),
    limit = 20;
  const records = useData<Page<Schema["AuditOut"]>>(
    ["admin-audit", offset],
    "/admin/audit?limit=" + limit + "&offset=" + offset,
  );
  return (
    <>
      <h2>Immutable audit history</h2>
      {records.isPending ? (
        <Loading />
      ) : records.error ? (
        <ErrorNotice error={records.error} />
      ) : (
        <section className="panel">
          <ul className="list">
            {records.data?.items.map((r) => (
              <li key={r.id}>
                <strong>{r.action.replaceAll("_", " ")}</strong>
                <p>{localTime(r.created_at)}</p>
                <small>Resource: {r.resource_id}</small>
                <details>
                  <summary>Decision details</summary>
                  <pre className="audit-details">
                    {JSON.stringify(r.details, null, 2)}
                  </pre>
                </details>
              </li>
            ))}
          </ul>
          {!records.data?.items.length && (
            <p>No administration actions recorded.</p>
          )}
        </section>
      )}
      <Pagination
        offset={offset}
        count={records.data?.items.length || 0}
        limit={limit}
        onChange={setOffset}
      />
    </>
  );
}
function EvaluationAdmin() {
  const outcomes = useData<Schema["Outcomes"]>(
      ["admin-outcomes"],
      "/admin/evaluation/outcomes",
    ),
    task = useTask();
  const [comparison, setComparison] = useState<Schema["Comparison"] | null>(
    null,
  );
  async function compare(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const result = await task.run(
      () =>
        api<Schema["Comparison"]>(
          "/admin/evaluation/requests/" + String(data.get("request_id")),
        ),
      "Comparison loaded.",
    );
    if (result) setComparison(result.value);
  }
  const percent = (n: number | null | undefined) =>
    n == null ? "No recorded data" : (n * 100).toFixed(1) + "%";
  return (
    <>
      <section className="panel">
        <h2>Recorded outcomes</h2>
        {outcomes.isPending ? (
          <Loading />
        ) : outcomes.error ? (
          <ErrorNotice error={outcomes.error} />
        ) : (
          outcomes.data && (
            <>
              <div className="table-wrap">
                <table>
                  <tbody>
                    <tr>
                      <th>Invited requests</th>
                      <td>{outcomes.data.invited_requests}</td>
                    </tr>
                    <tr>
                      <th>Scheduled sessions</th>
                      <td>{outcomes.data.scheduled_sessions}</td>
                    </tr>
                    <tr>
                      <th>Completed sessions</th>
                      <td>{outcomes.data.completed_sessions}</td>
                    </tr>
                    <tr>
                      <th>Acceptance rate</th>
                      <td>{percent(outcomes.data.acceptance_rate)}</td>
                    </tr>
                    <tr>
                      <th>Completion rate</th>
                      <td>{percent(outcomes.data.completion_rate)}</td>
                    </tr>
                    <tr>
                      <th>Mean recorded rating</th>
                      <td>
                        {outcomes.data.mean_review_stars?.toFixed(2) ||
                          "No reviews"}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <p className="hint">{outcomes.data.caveat}</p>
            </>
          )
        )}
      </section>
      <section className="panel admin-section">
        <h2>Compare matching algorithms</h2>
        <form className="inline-form" onSubmit={compare}>
          <Field label="Request ID">
            <input
              name="request_id"
              required
              maxLength={36}
              placeholder="Paste an existing request ID"
            />
          </Field>
          <button className="button secondary" disabled={task.busy}>
            Compare algorithms
          </button>
        </form>
        <Feedback task={task} />
        {comparison && (
          <>
            <p className="hint">{comparison.caveat}</p>
            {comparison.models.map((model) => (
              <div key={model.algorithm} className="admin-section">
                <h3>{model.algorithm}</h3>
                <p>
                  {model.elapsed_ms} ms · {model.candidates.length} displayed
                  candidates
                </p>
                <ol>
                  {model.candidates.map((c) => (
                    <li key={c.provider_id}>
                      <MemberName id={c.provider_id} /> · Score{" "}
                      {c.score.toFixed(3)} · {localTime(c.suggested_start)}
                    </li>
                  ))}
                </ol>
              </div>
            ))}
          </>
        )}
      </section>
    </>
  );
}
