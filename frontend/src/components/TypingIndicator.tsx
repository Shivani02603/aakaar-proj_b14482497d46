export default function TypingIndicator() {
  return (
    <span className="inline-flex gap-1 items-center px-2">
      {[0, 150, 300].map((d) => (
        <span key={d} className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: `${d}ms` }} />
      ))}
    </span>
  );
}
