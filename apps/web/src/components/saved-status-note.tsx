"use client";

/**
 * Shown when the student's saved items could not be read. Save controls stay
 * disabled (nothing is claimed about what is saved) until a retry succeeds.
 */
export default function SavedStatusNote({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="feed-note" role="status">
      <p>We couldn’t check your saved opportunities right now.</p>
      <button type="button" className="text-button" onClick={onRetry}>
        Try again
      </button>
    </div>
  );
}
