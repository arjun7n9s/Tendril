import { AccountDetailClient } from "./account-detail-client";

type Params = Promise<{ accountId: string }>;

export const dynamic = "force-dynamic";

export default async function AccountDetailPage({ params }: { params: Params }) {
  const { accountId } = await params;
  return <AccountDetailClient accountId={accountId} />;
}
