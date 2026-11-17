import PageLayout, { PageHeader } from "@/components/layout/PageLayout";
import { TaxOverview } from "@/components/tax/TaxOverview";

export default function TaxPage() {
  return (
    <PageLayout title="Tax" description="Tax records, ledger and actions by year">
      <PageHeader title="Tax" description="Records, ledger and correspondence by tax year" />
      <TaxOverview />
    </PageLayout>
  );
}
