import { afterEach, expect, it } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ProviderCard } from "./ProviderCard";
import type { Provider } from "../api/types";

afterEach(cleanup);
it("keeps a multi-skill member card and booking link aligned with the search", () => {
  const member: Provider = {
    id: "member",
    name: "Demo Member",
    city: null,
    campus: null,
    bio: "Peer learning.",
    offers: [
      { skill_id: "origami", name: "Origami", category: "Arts", level: 5 },
      { skill_id: "react", name: "React", category: "Technology", level: 4 },
    ],
    modes: ["ONLINE", "IN_PERSON"],
    rating_average: null,
    rating_count: 0,
    reputation_score: 50,
  };
  render(
    <MemoryRouter>
      <ProviderCard
        member={member}
        searchText="react"
        category="Technology"
        minLevel={4}
        mode="IN_PERSON"
      />
    </MemoryRouter>,
  );
  expect(screen.getByText("React", { exact: true })).toBeVisible();
  expect(screen.getByRole("link", { name: "View profile" })).toHaveAttribute(
    "href",
    "/members/member?skill=react&mode=IN_PERSON",
  );
  expect(screen.queryByText("Origami", { exact: true })).toBeNull();
  expect(screen.getByText("In person", { exact: true })).toBeVisible();
});
