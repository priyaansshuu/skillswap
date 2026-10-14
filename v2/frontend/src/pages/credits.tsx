import { useState } from "react";
import { Link } from "react-router-dom";
import { Page, Schema } from "../api/types";
import { useAuth } from "../auth-context";
import {
  ErrorNotice,
  Loading,
  localTime,
  minutes,
  Pagination,
  useData,
} from "../components/ui";

export function CreditSummary({ value }: { value: Schema["Wallet"] }) {
  return (
    <div className="credit-summary">
      <div>
        <span>Available to learn</span>
        <strong>{minutes(value.available_minutes)}</strong>
        <p>Ready for your next skill.</p>
      </div>
      <div>
        <span>Reserved for sessions</span>
        <strong>{minutes(value.reserved_minutes)}</strong>
        <p>Held until completion or cancellation.</p>
      </div>
      <div>
        <span>Total balance</span>
        <strong>{minutes(value.balance_minutes)}</strong>
        <p>Includes your reserved minutes.</p>
      </div>
    </div>
  );
}

export function Credits() {
  const auth = useAuth(),
    [offset, setOffset] = useState(0),
    limit = 20;
  const wallet = useData<Schema["Wallet"]>(
    ["wallet"],
    "/me/wallet",
    true,
    10000,
  );
  const ledger = useData<Page<Schema["CreditOut"]>>(
    ["ledger", offset],
    "/me/credits?limit=" + limit + "&offset=" + offset,
    true,
    10000,
  );
  return (
    <div className="container app-page">
      <h1>Your time credits</h1>
      <p>
        Every minute has equal value. Teaching earns minutes; learning spends
        them.
      </p>
      {wallet.isPending ? (
        <Loading />
      ) : wallet.error ? (
        <ErrorNotice error={wallet.error} />
      ) : (
        wallet.data && (
          <>
            <CreditSummary value={wallet.data} />
            <p>
              You have taught {minutes(wallet.data.taught_minutes)} in recorded
              completed sessions.
            </p>
          </>
        )
      )}
      <section className="panel">
        <h2>Transaction history</h2>
        {ledger.isPending ? (
          <Loading />
        ) : ledger.error ? (
          <ErrorNotice error={ledger.error} retry={ledger.refetch} />
        ) : ledger.data?.items.length ? (
          <ul className="list">
            {ledger.data.items.map((entry) => (
              <li key={entry.id}>
                <div className="row">
                  <div>
                    <strong>
                      {entry.kind === "GRANT"
                        ? "Starter minutes"
                        : entry.kind === "REVERSAL"
                          ? "Session correction"
                          : entry.receiver_id === auth.me?.id
                            ? "Minutes earned teaching"
                            : "Minutes used learning"}
                    </strong>
                    <p>{localTime(entry.created_at)}</p>
                    {entry.session_id && (
                      <Link to={"/sessions/" + entry.session_id}>
                        View session
                      </Link>
                    )}
                  </div>
                  <strong>
                    {entry.receiver_id === auth.me?.id ? "+" : "−"}
                    {entry.minutes} minutes
                  </strong>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p>No transactions recorded.</p>
        )}
      </section>
      <Pagination
        offset={offset}
        count={ledger.data?.items.length || 0}
        limit={limit}
        onChange={setOffset}
      />
    </div>
  );
}
