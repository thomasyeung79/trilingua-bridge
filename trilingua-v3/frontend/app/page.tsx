export default function LandingPage() {
  return (
    <main className="mx-auto max-w-4xl px-4 py-20 text-center">
      <h1 className="text-5xl font-bold tracking-tight">TriLingua Bridge</h1>
      <p className="mt-4 text-lg text-gray-600">AI-powered multilingual communication assistant.</p>
      <div className="mt-8 flex justify-center gap-4">
        <a href="/login" className="rounded-lg bg-blue-600 px-6 py-3 text-white font-semibold hover:bg-blue-700">
          Sign In
        </a>
        <a href="/register" className="rounded-lg border border-gray-300 px-6 py-3 font-semibold hover:bg-gray-100">
          Create Account
        </a>
      </div>
    </main>
  );
}
