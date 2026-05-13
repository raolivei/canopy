import { useState } from 'react';
import PageLayout from '../components/layout/PageLayout';
import { AssistantChat } from '../components/AssistantChat';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';

export default function AssistantPage() {
  const [conversationId, setConversationId] = useState<number | undefined>();

  return (
    <PageLayout title="AI Assistant">
      <div className="h-[calc(100vh-12rem)]">
        <Card className="h-full flex flex-col">
          <CardHeader>
            <CardTitle>Financial Assistant</CardTitle>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Ask questions about your transactions, spending, and portfolio
            </p>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col p-0">
            <AssistantChat
              conversationId={conversationId}
              onConversationStart={setConversationId}
            />
          </CardContent>
        </Card>
      </div>
    </PageLayout>
  );
}
