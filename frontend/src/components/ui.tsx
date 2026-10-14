import {
  cloneElement,
  useId,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertCircle, ArrowLeft, ArrowRight } from "lucide-react";
import { api, ApiError } from "../api/client";

export function useData<T>(
  key: readonly unknown[],
  path: string,
  enabled = true,
  poll?: number,
) {
  return useQuery({
    queryKey: key,
    queryFn: ({ signal }) => api<T>(path, { signal }),
    enabled,
    retry: false,
    refetchInterval: poll,
    refetchIntervalInBackground: false,
  });
}
export function useTask() {
  const client = useQueryClient();
  const [busy, setBusy] = useState(false),
    [error, setError] = useState<Error | null>(null),
    [message, setMessage] = useState("");
  const running = useRef(false);
  async function run<T>(
    action: () => Promise<T>,
    success = "Saved successfully.",
  ): Promise<{ value: T } | undefined> {
    if (running.current) return;
    running.current = true;
    setBusy(true);
    setError(null);
    setMessage("");
    try {
      const value = await action();
      setMessage(success);
      await client.invalidateQueries();
      return { value };
    } catch (e) {
      setError(e instanceof Error ? e : new Error("Try this action again."));
    } finally {
      running.current = false;
      setBusy(false);
    }
  }
  return {
    busy,
    error,
    message,
    run,
    clear: () => {
      setError(null);
      setMessage("");
    },
  };
}
export function Feedback({ task }: { task: ReturnType<typeof useTask> }) {
  return (
    <>
      {task.error && <ErrorNotice error={task.error} />}{" "}
      {task.message && (
        <p className="success" role="status">
          {task.message}
        </p>
      )}
    </>
  );
}
export function ErrorNotice({
  error,
  retry,
}: {
  error: Error | null;
  retry?: () => unknown;
}) {
  if (!error) return null;
  return (
    <div className="notice error" role="alert">
      <AlertCircle size={20} aria-hidden="true" />
      <div>
        <strong>{error.message}</strong>
        {error instanceof ApiError && error.details.length > 0 && (
          <ul>
            {error.details.map((d, i) => (
              <li key={i}>
                {d.field.replace("body.", "")}: {d.message}
              </li>
            ))}
          </ul>
        )}
        {retry && (
          <button className="text-button" onClick={() => retry()}>
            Try again
          </button>
        )}
      </div>
    </div>
  );
}
export function Loading({ text = "Loading SkillSwap…" }: { text?: string }) {
  return (
    <p className="loading" role="status">
      {text}
    </p>
  );
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children?: ReactNode;
}) {
  return (
    <div className="empty">
      <h3>{title}</h3>
      {children}
    </div>
  );
}
export function Field({
  label,
  children,
  hint,
}: {
  label: string;
  children: ReactElement<{ id?: string; "aria-describedby"?: string }>;
  hint?: string;
}) {
  const generatedId = useId();
  const inputId = children.props.id || generatedId;
  return (
    <div className="field">
      <label htmlFor={inputId}>{label}</label>
      {cloneElement(children, {
        id: inputId,
        "aria-describedby": hint
          ? generatedId + "-hint"
          : children.props["aria-describedby"],
      })}
      {hint && <small id={generatedId + "-hint"}>{hint}</small>}
    </div>
  );
}
export function Status({ value }: { value: string }) {
  return (
    <span className={"status status-" + value.toLowerCase()}>
      {value.replaceAll("_", " ").toLowerCase()}
    </span>
  );
}
export function Pagination({
  offset,
  count,
  limit,
  onChange,
}: {
  offset: number;
  count: number;
  limit: number;
  onChange: (n: number) => void;
}) {
  return (
    <nav className="pagination" aria-label="Pagination">
      <button
        className="button secondary"
        disabled={!offset}
        onClick={() => onChange(Math.max(0, offset - limit))}
      >
        <ArrowLeft size={16} />
        Previous
      </button>
      <span>Page {Math.floor(offset / limit) + 1}</span>
      <button
        className="button secondary"
        disabled={count < limit}
        onClick={() => onChange(offset + limit)}
      >
        Next
        <ArrowRight size={16} />
      </button>
    </nav>
  );
}
export function initials(name: string) {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((v) => v[0])
    .join("")
    .toUpperCase();
}
export function minutes(value: number) {
  const hours = Math.floor(value / 60),
    rest = value % 60;
  return (
    value +
    (value === 1 ? " minute" : " minutes") +
    (hours
      ? " · " +
        hours +
        " " +
        (hours === 1 ? "hour" : "hours") +
        (rest ? " " + rest + " min" : "")
      : "")
  );
}
export function localTime(value: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}
export const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
export function localInput(date: Date) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}
