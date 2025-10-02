import { CuratorForm } from "@/components/curator-form";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted">
      <div className="container mx-auto px-4 py-12">
        <div className="flex flex-col items-center justify-center space-y-8">
          <div className="text-center space-y-4 max-w-3xl">
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
              AI Curator Assistant
            </h1>
            <p className="text-lg text-muted-foreground">
              Transform your exhibition concept into a comprehensive proposal with AI-powered
              artist and artwork discovery
            </p>
          </div>

          <CuratorForm />
        </div>
      </div>
    </div>
  );
}
