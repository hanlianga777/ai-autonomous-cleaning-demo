export type PrototypeState =
  | "IDLE"
  | "DISCOVERED"
  | "EDGE_DETECTED"
  | "MULTI_VIEW"
  | "CLOUD_REVIEW"
  | "LOCATING"
  | "ROBOT_ASSIGNED"
  | "NAVIGATING"
  | "ELEVATOR_TRANSFER"
  | "SKYBRIDGE_TRANSFER"
  | "CLEANING"
  | "VERIFYING"
  | "CLOSED"
  | "HUMAN_FALLBACK";

export type Overlay = {
  label: string;
  confidence: number;
  bbox: [number, number, number, number];
};

export type Camera = {
  id: string;
  location: string;
  image: string;
  overlay?: Overlay[];
  temporary?: boolean;
};

export type DemoScenario = {
  id: "outdoor" | "liquid" | "can" | "oversized";
  triggerLabel: string;
  cameraId: string;
  eventTitle: string;
  category: string;
  confidence: number;
  qwenConfidence: number;
  qwenSummary: string;
  robot?: "Robot A" | "Robot B" | "Robot C";
  route?: string;
  afterImage?: string;
  steps: PrototypeState[];
};

export type ActiveEvent = {
  scenario: DemoScenario;
  stageIndex: number;
  startedAt: string;
};
