import { Link } from "react-router-dom";
import { ArrowRight, Calendar, Clock } from "lucide-react";
import { Page, RequestItem, Schema, SessionItem } from "../api/types";
import { useAuth } from "../auth-context";
import {
  Empty,
  ErrorNotice,
  Loading,
  localTime,
  minutes,
  Status,
  useData,
} from "../components/ui";
import { ActivityNav, MemberName, SkillName } from "./activity-shared";
import { CreditSummary } from "./credits";

export function Dashboard() {
  const auth = useAuth(),
    wallet = useData<Schema["Wallet"]>(["wallet"], "/me/wallet", true, 10000);
  const requests = useData<Page<RequestItem>>(
    ["dashboard-requests"],
    "/requests?limit=10",
    true,
    10000,
  );
  const sessions = useData<Page<SessionItem>>(
    ["dashboard-sessions"],
    "/sessions?limit=5&upcoming=true",
    true,
    10000,
  );
  const offers = useData<Page<Schema["UserSkillOut"]>>(
    ["dashboard-skills"],
    "/me/skills?limit=100",
  );
  return (
    <div className="container app-page">
      <div className="page-heading">
        <div>
          <h1>Your time, shared well</h1>
          <p>
            Welcome, {auth.me?.name.split(" ")[0]}. What will you learn or teach
            next?
          </p>
        </div>
        <Link className="button" to="/explore">
          Find a skill <ArrowRight size={18} />
        </Link>
      </div>
      <ActivityNav />
      {!offers.isPending &&
        !offers.error &&
        !offers.data?.items.some((s) => s.kind === "OFFER") && (
          <div className="intro-callout">
            <h2>Your teaching profile is a blank canvas</h2>
            <p>
              Add a skill and availability to help peers find you. You can learn
              with this same account.
            </p>
            <Link className="button secondary" to="/profile">
              Set up my skills
            </Link>
          </div>
        )}
      {wallet.error ? (
        <ErrorNotice error={wallet.error} />
      ) : (
        wallet.data && <CreditSummary value={wallet.data} />
      )}
      <div className="account-grid">
        <section className="panel">
          <h2>
            <Calendar size={23} /> Your sessions
          </h2>
          {sessions.isPending ? (
            <Loading />
          ) : sessions.error ? (
            <ErrorNotice error={sessions.error} />
          ) : sessions.data?.items.length ? (
            <ul className="list">
              {sessions.data.items.slice(0, 5).map((s) => (
                <li key={s.id}>
                  <div className="row">
                    <Link to={"/sessions/" + s.id}>
                      <strong>
                        <SkillName id={s.skill_id} />
                      </strong>
                    </Link>
                    <Status value={s.status} />
                  </div>
                  <p>{localTime(s.starts_at)}</p>
                  <small>
                    {s.provider_id === auth.me?.id
                      ? "You are teaching"
                      : "You are learning"}{" "}
                    ·{" "}
                    <MemberName
                      id={
                        s.provider_id === auth.me?.id
                          ? s.learner_id
                          : s.provider_id
                      }
                    />
                  </small>
                </li>
              ))}
            </ul>
          ) : (
            <Empty title="Your next session starts here">
              <Link to="/explore">Explore skills</Link>
            </Empty>
          )}
          <Link className="card-link" to="/sessions">
            View all sessions
          </Link>
        </section>
        <section className="panel">
          <h2>
            <Clock size={23} /> Session requests
          </h2>
          {requests.isPending ? (
            <Loading />
          ) : requests.error ? (
            <ErrorNotice error={requests.error} />
          ) : requests.data?.items.length ? (
            <ul className="list">
              {requests.data.items.slice(0, 5).map((r) => (
                <li key={r.id}>
                  <div className="row">
                    <Link to={"/requests/" + r.id}>
                      <strong>
                        <SkillName id={r.skill_id} />
                      </strong>
                    </Link>
                    <Status value={r.status} />
                  </div>
                  <p>
                    {r.provider_id === auth.me?.id
                      ? "Incoming teaching request"
                      : "Your learning request"}{" "}
                    · {minutes(r.duration_minutes)}
                  </p>
                </li>
              ))}
            </ul>
          ) : (
            <Empty title="No requests yet">
              <p>Choose a learning partner or add a skill you can teach.</p>
            </Empty>
          )}
          <Link className="card-link" to="/requests">
            View all requests
          </Link>
        </section>
      </div>
    </div>
  );
}
