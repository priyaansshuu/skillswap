import { useState } from "react";
import { Bell } from "lucide-react";
import { post } from "../api/client";
import { Page, Schema } from "../api/types";
import {
  Empty,
  ErrorNotice,
  Feedback,
  Loading,
  localTime,
  Pagination,
  useData,
  useTask,
} from "../components/ui";
import { ActivityNav } from "./activity-shared";

export function Notifications() {
  const [offset, setOffset] = useState(0),
    [unread, setUnread] = useState(false),
    task = useTask(),
    limit = 20;
  const notifications = useData<Page<Schema["NotificationOut"]>>(
    ["notifications", offset, unread],
    "/notifications?limit=" +
      limit +
      "&offset=" +
      offset +
      "&unread_only=" +
      unread,
    true,
    30000,
  );
  return (
    <div className="container app-page">
      <h1>
        <Bell size={34} /> Your notifications
      </h1>
      <ActivityNav />
      <label className="checkbox">
        <input
          type="checkbox"
          checked={unread}
          onChange={(e) => {
            setUnread(e.target.checked);
            setOffset(0);
          }}
        />
        Only unread notifications
      </label>
      <Feedback task={task} />
      {notifications.isPending ? (
        <Loading />
      ) : notifications.error ? (
        <ErrorNotice
          error={notifications.error}
          retry={notifications.refetch}
        />
      ) : notifications.data?.items.length ? (
        <section className="panel">
          <ul className="list">
            {notifications.data.items.map((n) => (
              <li className={n.is_read ? "" : "notification-unread"} key={n.id}>
                <div className="row">
                  <div>
                    <strong>{n.content}</strong>
                    <p>{localTime(n.created_at)}</p>
                  </div>
                  {!n.is_read && (
                    <button
                      className="text-button"
                      disabled={task.busy}
                      onClick={() =>
                        task.run(
                          () => post("/notifications/" + n.id + "/read"),
                          "Marked as read.",
                        )
                      }
                    >
                      Mark as read
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : (
        <Empty title="You’re all caught up">
          <p>New requests and session updates will appear here.</p>
        </Empty>
      )}
      <Pagination
        offset={offset}
        count={notifications.data?.items.length || 0}
        limit={limit}
        onChange={setOffset}
      />
    </div>
  );
}
