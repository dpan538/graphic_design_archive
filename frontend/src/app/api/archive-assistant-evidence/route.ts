import { NextResponse } from "next/server";
import { buildAssistantEvidence } from "@/lib/assistant-retrieval";

interface EvidenceRequest {
  question?: string;
  research?: boolean;
  context?: {
    surfaceId?: string;
    title?: string;
    dateText?: string;
    sourceName?: string;
  } | null;
}

export async function POST(request: Request) {
  const payload = await request.json() as EvidenceRequest;
  const question = payload.question?.trim() ?? "";
  if (!question || question.length > 2_000) {
    return NextResponse.json({ error: "A question between 1 and 2,000 characters is required." }, { status: 400 });
  }
  const evidence = buildAssistantEvidence(question, payload.context ?? undefined, {
    research: Boolean(payload.research),
  });
  return NextResponse.json(evidence);
}
