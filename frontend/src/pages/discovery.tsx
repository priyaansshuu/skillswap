import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  Link,
  useNavigate,
  useParams,
  useSearchParams,
} from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowRight,
  BookOpen,
  Code,
  Guitar,
  Languages,
  Palette,
  Search,
  SlidersHorizontal,
  X,
  Monitor,
} from "lucide-react";
import { allPages, post, put, query } from "../api/client";
import type { Page, Provider, RequestItem, Schema, Skill } from "../api/types";
import { useAuth } from "../auth-context";
import { ProviderCard } from "../components/ProviderCard";
import {
  Empty,
  ErrorNotice,
  Feedback,
  Field,
  initials,
  Loading,
  localInput,
  localTime,
  minutes,
  Pagination,
  timezone,
  useData,
  useTask,
} from "../components/ui";

export function useCatalog() {
  return useQuery({
    queryKey: ["catalog"],
    queryFn: ({ signal }) => allPages<Skill>("/public/skills", signal),
    staleTime: 60000,
  });
}
function SkillSearch({ small = false }: { small?: boolean }) {
  const [params] = useSearchParams(),
    [q, setQ] = useState(params.get("q") || ""),
    [mode, setMode] = useState(params.get("mode") ?? (small ? "" : "ONLINE"));
  const navigate = useNavigate(),
    catalog = useCatalog();
  useEffect(() => {
    setQ(params.get("q") || "");
    setMode(params.get("mode") ?? (small ? "" : "ONLINE"));
  }, [params, small]);
  function submit(e: FormEvent) {
    e.preventDefault();
    navigate("/explore?" + query({ q: q.trim(), mode }));
  }
  return (
    <form
      className={"skill-search " + (small ? "small" : "")}
      onSubmit={submit}
    >
      <label className="search-input">
        <Search size={25} aria-hidden="true" />
        <span className="sr-only">What do you want to learn?</span>
        <input
          list="search-skills"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="What do you want to learn?"
          maxLength={100}
        />
      </label>
      <datalist id="search-skills">
        {catalog.data?.map((s) => (
          <option key={s.id} value={s.name} />
        ))}
      </datalist>
      <label className="search-mode">
        <Monitor size={23} aria-hidden="true" />
        <span className="sr-only">Session mode</span>
        <select value={mode} onChange={(e) => setMode(e.target.value)}>
          <option value="ONLINE">Online</option>
          <option value="IN_PERSON">In person</option>
          <option value="">Any mode</option>
        </select>
      </label>
      <button className="button">
        Find a skill <ArrowRight size={20} />
      </button>
    </form>
  );
}
export function Home() {
  const auth = useAuth(),
    catalog = useCatalog(),
    members = useData<Page<Provider>>(
      ["featured", auth.loggedIn],
      "/public/providers?limit=3",
    );
  const categories = [
      ...new Set(catalog.data?.map((s) => s.category) || []),
    ].slice(0, 5),
    icons = [Code, Guitar, Languages, Palette, BookOpen];
  return (
    <div className="home">
      <section className="hero container">
        <h1>
          Learn something new.
          <br />
          Share what you know.
        </h1>
        <p>
          Your time is your currency. Find a skill, meet a peer, and learn
          together.
        </p>
        <SkillSearch />
        <nav className="subjects" aria-label="Skill categories">
          {categories.map((category, i) => {
            const Icon = icons[i];
            return (
              <Link key={category} to={"/explore?" + query({ category })}>
                <span>
                  <Icon size={20} />
                </span>
                {category}
              </Link>
            );
          })}
        </nav>
      </section>
      <section className="container featured">
        <div className="section-heading">
          <h2>Meet your next learning partner</h2>
          <Link to="/explore">
            Explore all skills <ArrowRight size={18} />
          </Link>
        </div>
        {members.isPending ? (
          <Loading text="Finding learning partners…" />
        ) : members.error ? (
          <ErrorNotice error={members.error} retry={members.refetch} />
        ) : members.data?.items.length ? (
          <div className="provider-grid">
            {members.data.items.map((member) => (
              <ProviderCard key={member.id} member={member} compact />
            ))}
          </div>
        ) : (
          <Empty title="The next learning partner could be you">
            <Link to="/profile">Add a skill you can teach.</Link>
          </Empty>
        )}
      </section>
      <section id="how-it-works" className="how-strip container">
        <div>
          <h2>Teach. Earn minutes. Learn.</h2>
          <p>Start with 120 minutes when you join SkillSwap.</p>
        </div>
        <ol>
          <li>
            <span>1</span>
            <div>
              <strong>Share a skill</strong>
              <p>Create a profile and tell us what you can teach.</p>
            </div>
          </li>
          <li>
            <span>2</span>
            <div>
              <strong>Earn time credits</strong>
              <p>Both confirm the session, then minutes transfer.</p>
            </div>
          </li>
          <li>
            <span>3</span>
            <div>
              <strong>Learn something new</strong>
              <p>Use your minutes to learn from a peer.</p>
            </div>
          </li>
        </ol>
        <Link className="button" to={auth.loggedIn ? "/profile" : "/register"}>
          {auth.loggedIn ? "Share a skill" : "Join SkillSwap"}{" "}
          <ArrowRight size={18} />
        </Link>
      </section>
    </div>
  );
}
export function Explore() {
  const [params, setParams] = useSearchParams(),
    auth = useAuth(),
    catalog = useCatalog(),
    dialog = useRef<HTMLDialogElement>(null);
  const offset = Number(params.get("offset") || 0),
    limit = 12;
  const path =
    "/public/providers?" +
    query({
      q: params.get("q") || "",
      skill_id: params.get("skill_id") || "",
      category: params.get("category") || "",
      city: params.get("city") || "",
      campus: params.get("campus") || "",
      mode: params.get("mode") || "",
      min_level: params.get("min_level") || "1",
      sort: params.get("sort") || "name",
      offset: Number.isFinite(offset) && offset >= 0 ? offset : 0,
      limit,
    });
  const members = useData<Page<Provider>>(
    ["providers", path, auth.loggedIn],
    path,
  );
  function update(key: string, value: string) {
    setParams((old) => {
      const next = new URLSearchParams(old);
      value ? next.set(key, value) : next.delete(key);
      if (key !== "offset") next.delete("offset");
      return next;
    });
  }
  function filters() {
    return (
      <>
        <h2>Filter skills</h2>
        <Field label="Skill">
          <select
            value={params.get("skill_id") || ""}
            onChange={(e) => update("skill_id", e.target.value)}
          >
            <option value="">All skills</option>
            {catalog.data?.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Category">
          <select
            value={params.get("category") || ""}
            onChange={(e) => update("category", e.target.value)}
          >
            <option value="">All categories</option>
            {[...new Set(catalog.data?.map((s) => s.category) || [])].map(
              (c) => (
                <option key={c}>{c}</option>
              ),
            )}
          </select>
        </Field>
        <Field label="Mode">
          <select
            value={params.get("mode") || ""}
            onChange={(e) => update("mode", e.target.value)}
          >
            <option value="">Any mode</option>
            <option value="ONLINE">Online</option>
            <option value="IN_PERSON">In person</option>
          </select>
        </Field>
        <Field label="City">
          <input
            value={params.get("city") || ""}
            onChange={(e) => update("city", e.target.value)}
            maxLength={100}
            placeholder="All cities"
          />
        </Field>
        <Field label="Campus">
          <input
            value={params.get("campus") || ""}
            onChange={(e) => update("campus", e.target.value)}
            maxLength={100}
            placeholder="All campuses"
          />
        </Field>
        <Field label="Minimum proficiency">
          <select
            value={params.get("min_level") || "1"}
            onChange={(e) => update("min_level", e.target.value)}
          >
            {[1, 2, 3, 4, 5].map((n) => (
              <option key={n} value={n}>
                {n === 1 ? "Any level" : n + " of 5"}
              </option>
            ))}
          </select>
        </Field>
        <button className="text-button" onClick={() => setParams({})}>
          Clear filters
        </button>
      </>
    );
  }
  return (
    <div className="container explore">
      <SkillSearch small />
      <h1>
        {params.get("q")
          ? "Find your " + params.get("q") + " learning partner"
          : "Find your learning partner"}
      </h1>
      <p className="page-intro">Share time. Build skills.</p>
      <div className="results-layout">
        <aside className="filters">{filters()}</aside>
        <dialog
          className="filter-dialog"
          ref={dialog}
          aria-label="Filter skills"
        >
          <button
            className="close-button"
            aria-label="Close filters"
            onClick={() => dialog.current?.close()}
          >
            <X />
          </button>
          {filters()}
          <button className="button" onClick={() => dialog.current?.close()}>
            Show results
          </button>
        </dialog>
        <section className="results" aria-label="Learning partners">
          <div className="results-toolbar">
            <button
              className="button secondary mobile-filters"
              onClick={() => dialog.current?.showModal()}
            >
              <SlidersHorizontal size={18} />
              Filters
            </button>
            <p>
              Choose a member, then check a time that works for both of you.
            </p>
            <label>
              <span className="sr-only">Sort members</span>
              <select
                value={params.get("sort") || "name"}
                onChange={(e) => update("sort", e.target.value)}
              >
                <option value="name">Name A–Z</option>
                <option value="name_desc">Name Z–A</option>
              </select>
            </label>
          </div>
          {members.isPending ? (
            <Loading />
          ) : members.error ? (
            <ErrorNotice error={members.error} retry={members.refetch} />
          ) : members.data?.items.length ? (
            <>
              <div className="provider-grid">
                {members.data.items.map((member) => (
                  <ProviderCard
                    key={member.id}
                    member={member}
                    skillId={params.get("skill_id") || undefined}
                    searchText={params.get("q") || ""}
                    category={params.get("category") || ""}
                    minLevel={Number(params.get("min_level") || 1)}
                    mode={params.get("mode") || ""}
                  />
                ))}
              </div>
              <Pagination
                offset={offset}
                count={members.data.items.length}
                limit={limit}
                onChange={(n) => update("offset", String(n))}
              />
            </>
          ) : (
            <Empty title="No learning partners found">
              <p>Try another skill, mode, or location.</p>
              <button
                className="button secondary"
                onClick={() => setParams({})}
              >
                Clear filters
              </button>
            </Empty>
          )}
        </section>
      </div>
    </div>
  );
}
export function MemberProfile() {
  const { id } = useParams(),
    [params] = useSearchParams(),
    auth = useAuth();
  const blockTask = useTask(),
    navigate = useNavigate();
  const member = useData<Provider>(
    ["provider", id, auth.loggedIn],
    "/public/providers/" + id,
  );
  if (member.isPending)
    return (
      <div className="container">
        <Loading />
      </div>
    );
  if (member.error)
    return (
      <div className="container">
        <ErrorNotice error={member.error} />
        <Link to="/explore">Back to discovery</Link>
      </div>
    );
  const p = member.data!;
  return (
    <div className="container member-page">
      <Link to="/explore" className="back-link">
        Back to learning partners
      </Link>
      <div className="profile-layout">
        <article>
          <div className="profile-identity">
            <span className="avatar large" aria-hidden="true">
              {initials(p.name)}
            </span>
            <div>
              <h1>{p.name}</h1>
              <p>
                {[p.city, p.campus].filter(Boolean).join(" · ") ||
                  "Location not added"}
              </p>
              <p>
                {p.modes
                  .map((m) => (m === "ONLINE" ? "Online" : "In person"))
                  .join(" · ") || "Availability not added"}
              </p>
            </div>
          </div>
          <h2>About me</h2>
          <p className="profile-bio">
            {p.bio || "This member has not added a bio yet."}
          </p>
          <h2>Skills I can share</h2>
          <ul className="offer-list">
            {p.offers.map((o) => (
              <li key={o.skill_id}>
                <strong>{o.name}</strong>
                <span>
                  {o.category} · Proficiency {o.level} of 5
                </span>
              </li>
            ))}
          </ul>
          <div className="trust-summary">
            <div>
              <h2>Teaching reviews</h2>
              <p>
                {p.rating_count
                  ? p.rating_average?.toFixed(1) +
                    " / 5 from " +
                    p.rating_count +
                    " reviews"
                  : "No reviews yet"}
              </p>
            </div>
            <div>
              <h2>Reputation</h2>
              <p>{p.reputation_score.toFixed(1)} / 100</p>
              <small>
                Based on recorded activity and feedback; separate from review
                stars.
              </small>
            </div>
          </div>
          {auth.loggedIn && auth.me?.id !== p.id && (
            <>
              <button
                className="text-button"
                disabled={blockTask.busy}
                onClick={async () => {
                  const result = await blockTask.run(
                    () => put("/me/blocks/" + p.id, undefined),
                    "Member blocked.",
                  );
                  if (result) navigate("/explore");
                }}
              >
                Block this member
              </button>
              <Feedback task={blockTask} />
            </>
          )}
        </article>
        <aside className="booking-panel">
          {auth.me?.id === p.id ? (
            <>
              <h2>Your teaching profile</h2>
              <Link className="button" to="/profile">
                Edit skills and availability
              </Link>
            </>
          ) : (
            <BookingForm
              provider={p}
              initialSkill={params.get("skill") || p.offers[0]?.skill_id}
              initialMode={
                params.get("mode") ||
                (p.modes.includes("ONLINE") ? "ONLINE" : "IN_PERSON")
              }
            />
          )}
        </aside>
      </div>
    </div>
  );
}
function BookingForm({
  provider,
  initialSkill,
  initialMode,
}: {
  provider: Provider;
  initialSkill: string;
  initialMode: string;
}) {
  const auth = useAuth(),
    navigate = useNavigate(),
    task = useTask(),
    [skill, setSkill] = useState(initialSkill);
  const [duration, setDuration] = useState(30),
    [mode, setMode] = useState(
      initialMode === "IN_PERSON" ? "IN_PERSON" : "ONLINE",
    );
  const [start, setStart] = useState(
      localInput(new Date(Date.now() + 3600000)),
    ),
    [end, setEnd] = useState(localInput(new Date(Date.now() + 86400000)));
  const [preview, setPreview] = useState<Schema["RequestPreview"] | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const submission = useRef<{ body: string; key: string } | null>(null);
  useEffect(() => {
    setPreview(null);
    setConfirmed(false);
    task.clear();
  }, [skill, duration, mode, start, end]);
  function payload() {
    return {
      skill_id: skill,
      provider_id: provider.id,
      duration_minutes: duration,
      mode: mode as "ONLINE" | "IN_PERSON",
      window_start: new Date(start).toISOString(),
      window_end: new Date(end).toISOString(),
    };
  }
  async function check(e: FormEvent) {
    e.preventDefault();
    const response = await task.run(
      () => post<Schema["RequestPreview"]>("/requests/preview", payload()),
      "Availability checked.",
    );
    if (response) setPreview(response.value);
  }
  async function send() {
    const body = payload(),
      encoded = JSON.stringify(body);
    if (submission.current?.body !== encoded)
      submission.current = { body: encoded, key: crypto.randomUUID() };
    const response = await task.run(
      () =>
        post<RequestItem>("/requests", body, {
          "Idempotency-Key": submission.current!.key,
        }),
      "Request sent.",
    );
    if (response) navigate("/requests/" + response.value.id);
  }
  if (!auth.loggedIn)
    return (
      <>
        <h2>Learn with {provider.name.split(" ")[0]}</h2>
        <p>Log in to check availability and request a session.</p>
        <Link
          className="button"
          to={
            "/login?returnTo=" +
            encodeURIComponent(
              "/members/" +
                provider.id +
                "?skill=" +
                initialSkill +
                "&mode=" +
                mode,
            )
          }
        >
          Log in to request
        </Link>
        <p>
          <Link to="/register">New here? Join with 120 minutes.</Link>
        </p>
      </>
    );
  return (
    <>
      <h2>Request a session</h2>
      <p>Every minute of learning uses one time credit.</p>
      <form onSubmit={check}>
        <Field label="Skill">
          <select value={skill} onChange={(e) => setSkill(e.target.value)}>
            {provider.offers.map((o) => (
              <option key={o.skill_id} value={o.skill_id}>
                {o.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Duration in minutes">
          <input
            type="number"
            min={1}
            max={480}
            required
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
          />
        </Field>
        <Field label="Session mode">
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="ONLINE">Online</option>
            <option value="IN_PERSON">In person</option>
          </select>
        </Field>
        <Field label="Window starts">
          <input
            type="datetime-local"
            required
            value={start}
            onChange={(e) => setStart(e.target.value)}
          />
        </Field>
        <Field label="Window ends">
          <input
            type="datetime-local"
            required
            value={end}
            min={start}
            onChange={(e) => setEnd(e.target.value)}
          />
        </Field>
        <small>
          Times are shown in {timezone}. Your window must fit the duration and
          be within 30 days.
        </small>
        <button className="button secondary full" disabled={task.busy}>
          Check availability
        </button>
      </form>
      <Feedback task={task} />
      {preview && (
        <div className="preview-result">
          {preview.eligible ? (
            <>
              <h3>A time that works</h3>
              <p>{localTime(preview.candidates[0].suggested_start)}</p>
              <p>
                {minutes(duration)} requested ·{" "}
                {minutes(preview.available_minutes)} available
              </p>
              <small>
                Teacher acceptance is required. Credits are reserved only when
                they accept.
              </small>
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={confirmed}
                  onChange={(e) => setConfirmed(e.target.checked)}
                />
                I’m happy with this suggested time.
              </label>
              <button
                className="button full"
                disabled={task.busy || !confirmed}
                onClick={send}
              >
                {task.busy ? "Sending…" : "Send session request"}
              </button>
            </>
          ) : (
            <p>{preview.reason}</p>
          )}
        </div>
      )}
    </>
  );
}
