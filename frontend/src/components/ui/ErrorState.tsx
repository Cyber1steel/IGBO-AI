import { RefreshCw } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";

export function ErrorState({
  message = "Something went wrong loading this.",
  onRetry,
}: {
  message?: string;
  onRetry: () => void;
}) {
  return (
    <Card className="text-center py-10">
      <p className="text-ink-soft mb-4">{message}</p>
      <Button variant="secondary" size="sm" icon={<RefreshCw size={14} />} onClick={onRetry}>
        Try again
      </Button>
    </Card>
  );
}
