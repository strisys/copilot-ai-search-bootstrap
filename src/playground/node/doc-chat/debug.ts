import debug, { IDebugger } from 'debug';
export type { IDebugger as ILogger };

if ("window" in globalThis) {
  console.error(`NOTE:\ndebug.js (https://debugjs.net), if running in browser or electron, will use console.debug for Chrome. These log entries will not show if being filtered out by Chrome itself.\nThe filtering in Chrome is at the top on the Console tab in devtools (F12).  In the All Levels dropdown choose Verbose.
  `)
}

export const getLogger = (namespace: (string | null) = null): IDebugger => {
  const ns = ((!namespace) ? '*' : (((namespace.endsWith(':*')) ? namespace : `${namespace}:*`)));

  // NOTE: debug.js, if running in browser/electron will use console.debug for Chrome.
  // These will not show if being filtered out by Chrome itself.
  // If the log message not shown in Chrome make sure they are not being filtered out.
  // The filtering is at the top on the Console tab.  With All Levels choose verbose.
  // https://stackoverflow.com/questions/18760213/chrome-console-log-console-debug-are-not-working
  const d: IDebugger = debug(ns);
  d.enabled = true;

  return d;
};