import { NavLink } from "react-router-dom";
import { Schema } from "../api/types";
import { useCatalog } from "./discovery";
import { useData } from "../components/ui";

export function ActivityNav() {
  return (
    <nav className="activity-tabs" aria-label="Your activity">
      <NavLink to="/dashboard">Overview</NavLink>
      <NavLink to="/requests">Requests</NavLink>
      <NavLink to="/sessions">Sessions</NavLink>
      <NavLink to="/notifications">Notifications</NavLink>
    </nav>
  );
}

export function MemberName({ id }: { id: string }) {
  const name = useData<Schema["PublicProfile"]>(
    ["member-name", id],
    "/users/" + id,
  );
  return (
    <>{name.data?.name || (name.error ? "Member unavailable" : "Member")}</>
  );
}

export function SkillName({ id }: { id: string }) {
  const skills = useCatalog();
  return <>{skills.data?.find((s) => s.id === id)?.name || "Skill session"}</>;
}
