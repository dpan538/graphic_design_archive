import "server-only";

import { getOpenInquiryRegistry } from "./registry.server.ts";
import {
  TRACE_OPEN_INQUIRY_API_VERSION,
  TRACE_OPEN_INQUIRY_LAYER,
  TRACE_OPEN_INQUIRY_RESPONSE_SCHEMA_VERSION,
} from "./types.ts";
import type {
  OpenInquiryBoundary,
  OpenInquiryDetailData,
  OpenInquiryErrorCode,
  OpenInquiryListData,
  OpenInquiryResponseEnvelope,
  OpenInquiryServiceResult,
} from "./types.ts";

const INQUIRY_ID_PATTERN = /^R16B-(?:SCOPED-)?HYPOTHESIS:[0-9a-f]{64}$/u;

const OPEN_INQUIRY_BOUNDARY: OpenInquiryBoundary = Object.freeze({
  evidence_bounded: true,
  validated_layer_contamination_allowed: false,
  implicit_pair_projection_allowed: false,
  validated_topology_mutation_allowed: false,
  stochastic_display: false,
});

function success<T>(data: T): OpenInquiryServiceResult<T> {
  const registry = getOpenInquiryRegistry();
  const envelope: OpenInquiryResponseEnvelope<T> = {
    schema_version: TRACE_OPEN_INQUIRY_RESPONSE_SCHEMA_VERSION,
    api_version: TRACE_OPEN_INQUIRY_API_VERSION,
    layer: TRACE_OPEN_INQUIRY_LAYER,
    registry_sha256: registry.records_sha256,
    boundary: OPEN_INQUIRY_BOUNDARY,
    data,
  };
  return { ok: true, data: envelope };
}

export function openInquiryFailure(
  code: OpenInquiryErrorCode,
  message: string,
  status: number,
  retryable = false,
): OpenInquiryServiceResult<never> {
  return { ok: false, code, message, status, retryable };
}

export function listOpenInquiries(): OpenInquiryServiceResult<OpenInquiryListData> {
  const registry = getOpenInquiryRegistry();
  return success({
    count: registry.counts.scoped_higher_order_hypothesis_count,
    items: registry.records,
  });
}

export function retrieveOpenInquiry(
  inquiryId: string,
): OpenInquiryServiceResult<OpenInquiryDetailData> {
  if (!INQUIRY_ID_PATTERN.test(inquiryId)) {
    return openInquiryFailure(
      "OPEN_INQUIRY_NOT_FOUND",
      "The requested Open Inquiry record does not exist.",
      404,
    );
  }
  const item = getOpenInquiryRegistry().records.find((record) => record.inquiry_id === inquiryId);
  if (!item) {
    return openInquiryFailure(
      "OPEN_INQUIRY_NOT_FOUND",
      "The requested Open Inquiry record does not exist.",
      404,
    );
  }
  return success({ item });
}
