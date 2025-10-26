import { AgentExplorer } from "@/components/AgentExplorer";
import { CopilotChat } from "@copilotkit/react-ui";

import styles from "./page.module.css";

export default function Home() {
  return (
    <div className={styles.page}>
      <main className={styles.main}>
        <section className={styles.section}>
          <header className={styles.header}>
            <h1>Emergency Response Console</h1>
            <p>
              Discover the local A2A agents, inspect their capabilities, and send
              them messages directly from the browser.
            </p>
          </header>
          <AgentExplorer />
        </section>
        <aside className={styles.chatPanel}>
          <CopilotChat
            instructions="You are the operations coordinator. Help the user route requests to the correct emergency response agent and keep conversations concise."
            labels={{
              title: "Operations Copilot",
              initial: "Hi! Which situation do you need help with today?",
            }}
          />
        </aside>
      </main>
    </div>
  );
}
