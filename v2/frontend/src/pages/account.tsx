import { useState, type FormEvent } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import { allPages, api, patch, post, put, remove } from "../api/client";
import type { Me, Schema, Suggestion } from "../api/types";
import { useAuth } from "../auth-context";
import { useCatalog } from "./discovery";
import {
  ErrorNotice,
  Feedback,
  Field,
  Loading,
  localTime,
  Status,
  timezone,
  useTask,
} from "../components/ui";

export function AuthPage({ register = false }: { register?: boolean }) {
  const auth = useAuth(),
    navigate = useNavigate(),
    [params] = useSearchParams(),
    task = useTask();
  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    const response = await task.run(
      async () => {
        const email = String(data.get("email")).trim(),
          password = String(data.get("password"));
        if (register)
          await post<Me>("/auth/register", {
            name: String(data.get("name")).trim(),
            email,
            password,
          });
        return api<Schema["Token"]>("/auth/token", {
          method: "POST",
          body: new URLSearchParams({ username: email, password }),
        });
      },
      register ? "Account created." : "Welcome back.",
    );
    if (response) {
      auth.login(response.value.access_token, response.value.expires_in);
      const target = params.get("returnTo") || "";
      navigate(
        target.startsWith("/") && !target.startsWith("//")
          ? target
          : register
            ? "/profile"
            : "/dashboard",
        { replace: true },
      );
    }
  }
  const suffix = params.get("returnTo")
    ? "?returnTo=" + encodeURIComponent(params.get("returnTo")!)
    : "";
  return (
    <section className="auth-page">
      <h1>{register ? "Join SkillSwap" : "Welcome back"}</h1>
      <p>
        {register
          ? "One account to teach, learn, and share time. Start with 120 minutes."
          : "Your next skill is waiting. Log in to continue."}
      </p>
      <form onSubmit={submit}>
        {register && (
          <Field label="Your name">
            <input name="name" autoComplete="name" required maxLength={100} />
          </Field>
        )}
        <Field label="Email">
          <input
            name="email"
            type="email"
            autoComplete="username"
            required
            maxLength={254}
          />
        </Field>
        <Field label="Password" hint={register ? "Use 12–128 characters." : ""}>
          <input
            name="password"
            type="password"
            autoComplete={register ? "new-password" : "current-password"}
            minLength={register ? 12 : undefined}
            maxLength={128}
            required
          />
        </Field>
        <button className="button" disabled={task.busy}>
          {task.busy
            ? "Opening your account…"
            : register
              ? "Create my account"
              : "Log in"}
        </button>
      </form>
      <Feedback task={task} />
      <p className="auth-switch">
        {register ? "Already a member? " : "New to SkillSwap? "}
        <Link to={(register ? "/login" : "/register") + suffix}>
          {register ? "Log in" : "Join SkillSwap"}
        </Link>
      </p>
    </section>
  );
}
export function ProfileEditor() {
  const auth = useAuth(),
    task = useTask();
  async function save(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const data = new FormData(e.currentTarget);
    await task.run(() =>
      patch<Me>("/me", {
        name: String(data.get("name")),
        city: String(data.get("city")).trim() || null,
        campus: String(data.get("campus")).trim() || null,
        bio: String(data.get("bio")),
      }),
    );
  }
  return (
    <div className="container app-page">
      <div className="page-heading">
        <div>
          <h1>Make your profile yours</h1>
          <p>Teach what you know. Choose what you want to learn.</p>
        </div>
        <Link className="button secondary" to="/explore">
          Explore skills
        </Link>
      </div>
      <div className="account-grid">
        <div className="stack">
          <section className="panel">
            <h2>Your details</h2>
            <form onSubmit={save}>
              <div className="form-grid">
                <Field label="Name">
                  <input
                    name="name"
                    defaultValue={auth.me?.name}
                    required
                    maxLength={100}
                  />
                </Field>
                <Field label="Email">
                  <input value={auth.me?.email || ""} readOnly type="email" />
                </Field>
                <Field label="City">
                  <input
                    name="city"
                    defaultValue={auth.me?.city || ""}
                    maxLength={100}
                  />
                </Field>
                <Field label="Campus">
                  <input
                    name="campus"
                    defaultValue={auth.me?.campus || ""}
                    maxLength={100}
                  />
                </Field>
                <div className="wide">
                  <Field label="About you">
                    <textarea
                      name="bio"
                      defaultValue={auth.me?.bio || ""}
                      maxLength={1000}
                      placeholder="Tell other members what you enjoy sharing."
                    />
                  </Field>
                </div>
              </div>
              <button className="button" disabled={task.busy}>
                Save profile
              </button>
            </form>
            <Feedback task={task} />
          </section>
          <AvailabilityEditor />
          <SkillSuggestions />
        </div>
        <div className="stack">
          <SkillEditor kind="OFFER" />
          <SkillEditor kind="WANT" />
          <BlockedMembers />
        </div>
      </div>
    </div>
  );
}
function SkillEditor({ kind }: { kind: "OFFER" | "WANT" }) {
  const catalog = useCatalog(),
    task = useTask(),
    [skill, setSkill] = useState(""),
    [level, setLevel] = useState(kind === "OFFER" ? 3 : 1);
  const entries = useQuery({
    queryKey: ["my-skills"],
    queryFn: ({ signal }) =>
      allPages<Schema["UserSkillOut"]>("/me/skills", signal),
  });
  async function add(e: FormEvent) {
    e.preventDefault();
    const response = await task.run(() =>
      put("/me/skills", { skill_id: skill, kind, level }),
    );
    if (response) setSkill("");
  }
  const rows = entries.data?.filter((s) => s.kind === kind) || [];
  return (
    <section className="panel">
      <h2>
        {kind === "OFFER" ? "Skills I can teach" : "Skills I want to learn"}
      </h2>
      {entries.isPending ? (
        <Loading />
      ) : entries.error ? (
        <ErrorNotice error={entries.error} retry={entries.refetch} />
      ) : rows.length ? (
        <ul className="chip-list">
          {rows.map((s) => (
            <li key={s.skill_id}>
              <span>
                {catalog.data?.find((c) => c.id === s.skill_id)?.name ||
                  "Skill"}{" "}
                · Level {s.level}
              </span>
              <button
                aria-label={
                  "Remove " +
                  (catalog.data?.find((c) => c.id === s.skill_id)?.name ||
                    "skill")
                }
                disabled={task.busy}
                onClick={() =>
                  task.run(
                    () => remove("/me/skills/" + s.skill_id + "/" + kind),
                    "Skill removed.",
                  )
                }
              >
                <X size={17} />
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="hint">
          {kind === "OFFER"
            ? "Add your first teaching skill to appear in discovery."
            : "Choose a skill you would love to learn."}
        </p>
      )}
      <form onSubmit={add}>
        <Field label={kind === "OFFER" ? "Teaching skill" : "Learning goal"}>
          <select
            required
            value={skill}
            onChange={(e) => setSkill(e.target.value)}
          >
            <option value="">Choose a skill</option>
            {catalog.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label={kind === "OFFER" ? "Your proficiency" : "Target level"}>
          <select
            value={level}
            onChange={(e) => setLevel(Number(e.target.value))}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n} of 5{n === 1 ? " · Beginner" : n === 5 ? " · Advanced" : ""}
              </option>
            ))}
          </select>
        </Field>
        <button className="button secondary" disabled={task.busy || !skill}>
          <Plus size={17} />
          Add skill
        </button>
      </form>
      <Feedback task={task} />
      {catalog.error && <ErrorNotice error={catalog.error} />}
    </section>
  );
}
function AvailabilityEditor() {
  const task = useTask();
  const slots = useQuery({
    queryKey: ["availability"],
    queryFn: ({ signal }) =>
      allPages<Schema["AvailabilityOut"]>("/me/availability", signal),
  });
  async function add(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      data = new FormData(form);
    const response = await task.run(
      () =>
        post("/me/availability", {
          starts_at: new Date(String(data.get("starts_at"))).toISOString(),
          ends_at: new Date(String(data.get("ends_at"))).toISOString(),
          mode: String(data.get("mode")),
        }),
      "Availability added.",
    );
    if (response) form.reset();
  }
  return (
    <section className="panel">
      <h2>When can you teach?</h2>
      <p className="hint">
        Add dated time windows. Times are shown in {timezone}.
      </p>
      {slots.isPending ? (
        <Loading />
      ) : slots.error ? (
        <ErrorNotice error={slots.error} />
      ) : slots.data?.length ? (
        <ul className="list">
          {slots.data.map((s) => (
            <li key={s.id}>
              <div className="row">
                <div>
                  <strong>
                    {s.mode === "ONLINE" ? "Online" : "In person"}
                  </strong>
                  <p>
                    {localTime(s.starts_at)} — {localTime(s.ends_at)}
                  </p>
                  {new Date(s.ends_at) < new Date() && (
                    <small>This window has ended.</small>
                  )}
                </div>
                <button
                  className="text-button"
                  disabled={task.busy}
                  onClick={() =>
                    task.run(
                      () => remove("/me/availability/" + s.id),
                      "Availability removed.",
                    )
                  }
                >
                  Remove
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>No availability yet. Add a window so peers can request a session.</p>
      )}
      <form className="availability-form" onSubmit={add}>
        <Field label="Available from">
          <input name="starts_at" type="datetime-local" required />
        </Field>
        <Field label="Available until">
          <input name="ends_at" type="datetime-local" required />
        </Field>
        <Field label="Teaching mode">
          <select name="mode">
            <option value="ONLINE">Online</option>
            <option value="IN_PERSON">In person</option>
          </select>
        </Field>
        <button className="button secondary" disabled={task.busy}>
          Add availability
        </button>
      </form>
      <Feedback task={task} />
    </section>
  );
}
function SkillSuggestions() {
  const task = useTask();
  const suggestions = useQuery({
    queryKey: ["my-suggestions"],
    queryFn: ({ signal }) => allPages<Suggestion>("/skill-suggestions", signal),
  });
  async function send(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget,
      data = new FormData(form);
    const response = await task.run(
      () =>
        post("/skill-suggestions", {
          name: String(data.get("name")),
          explanation: String(data.get("explanation")),
        }),
      "Suggestion sent for admin review.",
    );
    if (response) form.reset();
  }
  return (
    <section className="panel">
      <h2>Missing a skill?</h2>
      <p>
        Suggest it for the catalog. An admin will check the name and category
        before you can add it.
      </p>
      <form onSubmit={send}>
        <Field label="Suggested skill name">
          <input name="name" required maxLength={100} />
        </Field>
        <Field label="Why would you like to add it?">
          <textarea name="explanation" maxLength={1000} />
        </Field>
        <button className="button secondary" disabled={task.busy}>
          Suggest a skill
        </button>
      </form>
      <Feedback task={task} />
      {suggestions.error && <ErrorNotice error={suggestions.error} />}
      <ul className="list">
        {suggestions.data?.map((s) => (
          <li key={s.id}>
            <div className="row">
              <strong>{s.name}</strong>
              <Status value={s.status} />
            </div>
            {s.resolution && <p>{s.resolution}</p>}
            {s.status === "APPROVED" && (
              <small>Now available in the skill selectors above.</small>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
function BlockedMembers() {
  const task = useTask();
  const blocked = useQuery({
    queryKey: ["blocks"],
    queryFn: ({ signal }) =>
      allPages<Schema["PublicProfile"]>("/me/blocks", signal),
  });
  return (
    <section className="panel">
      <h2>Blocked members</h2>
      <p className="hint">
        Blocked members are excluded from your signed-in discovery and matching.
      </p>
      {blocked.isPending ? (
        <Loading />
      ) : blocked.error ? (
        <ErrorNotice error={blocked.error} />
      ) : blocked.data?.length ? (
        <ul className="list">
          {blocked.data.map((m) => (
            <li key={m.id} className="row">
              <strong>{m.name}</strong>
              <button
                className="text-button"
                disabled={task.busy}
                onClick={() =>
                  task.run(
                    () => remove("/me/blocks/" + m.id),
                    "Member unblocked.",
                  )
                }
              >
                Unblock
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p>You haven’t blocked any members.</p>
      )}
      <Feedback task={task} />
    </section>
  );
}
