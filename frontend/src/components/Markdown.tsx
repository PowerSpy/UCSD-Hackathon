import ReactMarkdown from "react-markdown";

type Props = { children: string; className?: string };

export function Markdown({ children, className }: Props) {
  return (
    <div className={className}>
      <ReactMarkdown
        components={{
          p: ({ children: c }) => <p className="mb-3 last:mb-0 leading-relaxed text-lg">{c}</p>,
          strong: ({ children: c }) => <strong className="font-semibold text-sageDark">{c}</strong>,
          ul: ({ children: c }) => <ul className="mb-3 list-disc pl-6 last:mb-0">{c}</ul>,
          ol: ({ children: c }) => <ol className="mb-3 list-decimal pl-6 last:mb-0">{c}</ol>,
          li: ({ children: c }) => <li className="mb-1">{c}</li>,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
