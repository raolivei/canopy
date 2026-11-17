/** Names the account labels an import defaulted or skipped (#144). */
export function AccountLabelNotes({
  defaulted,
  skipped,
}: {
  defaulted: string[];
  skipped: string[];
}) {
  if (defaulted.length === 0 && skipped.length === 0) return null;
  return (
    <div className="mt-3 space-y-1 text-xs">
      {defaulted.length > 0 && (
        <div className="text-warning-700 dark:text-warning-300">
          <span className="font-medium">Imported as cash accounts:</span>{" "}
          {defaulted.join(", ")}. These labels carry no account type; change the
          type on the Accounts page if one is wrong.
        </div>
      )}
      {skipped.length > 0 && (
        <div className="text-danger-700 dark:text-danger-300">
          <span className="font-medium">Skipped accounts:</span>{" "}
          {skipped.join(", ")}
        </div>
      )}
    </div>
  );
}
