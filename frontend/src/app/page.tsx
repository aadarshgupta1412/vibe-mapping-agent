import { Chat } from "@/components/chat/chat";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-4">
      <div className="w-full max-w-5xl">
        <h1 className="text-2xl font-bold text-center mb-4">Vibe Mapping Agent</h1>
        <p className="text-center mb-6">Tell me what kind of clothing you&apos;re looking for!</p>
        <Chat />
      </div>
    </main>
  );
}
