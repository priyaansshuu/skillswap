import { Link } from "react-router-dom";
import { ArrowRight, Monitor, Star, MapPin } from "lucide-react";
import type { Provider } from "../api/types";
import { initials } from "./ui";

export function ProviderCard({
  member,
  compact = false,
  skillId,
  searchText = "",
  category = "",
  minLevel = 1,
  mode = "",
}: {
  member: Provider;
  compact?: boolean;
  skillId?: string;
  searchText?: string;
  category?: string;
  minLevel?: number;
  mode?: string;
}) {
  const relevant = member.offers.filter(
    (o) =>
      (!skillId || o.skill_id === skillId) &&
      (!category || o.category === category) &&
      o.level >= minLevel,
  );
  const offer =
    relevant.find(
      (o) =>
        searchText &&
        o.name.toLocaleLowerCase().includes(searchText.toLocaleLowerCase()),
    ) ||
    relevant[0] ||
    member.offers[0];
  const displayMode =
    mode ||
    (member.modes.includes("ONLINE")
      ? "ONLINE"
      : member.modes.includes("IN_PERSON")
        ? "IN_PERSON"
        : "");
  const hue =
    member.name.split("").reduce((a, c) => a + c.charCodeAt(0), 0) % 4;
  return (
    <article className={"provider-card " + (compact ? "compact" : "")}>
      <div className={"member-heading hue-" + hue}>
        <div className="avatar" aria-hidden="true">
          {initials(member.name)}
        </div>
        {compact && (
          <div>
            <h3>{member.name}</h3>
            <p>{offer?.name}</p>
            <small>
              {member.modes
                .map((m) => (m === "ONLINE" ? "Online" : "In person"))
                .join(" · ") || "Availability not added"}
            </small>
          </div>
        )}
      </div>
      {!compact && <h3>{member.name}</h3>}
      {!compact && (
        <p className="card-meta">
          <span>{offer?.name}</span>
          {displayMode === "ONLINE" ? (
            <span>
              <Monitor size={16} />
              Online
            </span>
          ) : displayMode === "IN_PERSON" ? (
            <span>
              <MapPin size={16} />
              In person
            </span>
          ) : (
            <span>Availability not added</span>
          )}
        </p>
      )}
      <p className="rating">
        {member.rating_count ? (
          <>
            <Star size={15} aria-hidden="true" />
            {member.rating_average?.toFixed(1)} · {member.rating_count}{" "}
            {member.rating_count === 1 ? "review" : "reviews"}
          </>
        ) : (
          "No reviews yet"
        )}
      </p>
      {!compact && (
        <small>
          Proficiency: {offer?.level} of 5
          {member.city ? " · " + member.city : ""}
        </small>
      )}
      <p className="bio">
        {member.bio ||
          "Meet this member and explore the skills they can share."}
      </p>
      <Link
        className={compact ? "profile-button" : "card-link"}
        to={
          "/members/" +
          member.id +
          (offer ? "?skill=" + offer.skill_id : "") +
          (mode ? "&mode=" + mode : "")
        }
      >
        View profile <ArrowRight size={18} />
      </Link>
    </article>
  );
}
