
let setModalState:
  | ((state: { path: string; status: number } | null) => void)
  | null = null;

export function registerUnauthorizedModalSetter(
  fn: (state: { path: string; status: number } | null) => void
) {
  setModalState = fn;
}

export function triggerUnauthorizedModal(path: string, status: number) {
  if (setModalState) {
    setModalState({ path, status });
  } else {
    console.warn("No modal handler registered for unauthorized request.");
  }
}
