import { InputHTMLAttributes } from "react";

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export function Field({ label, error, id, ...props }: FieldProps) {
  return (
    <div className="mb-4">
      <label htmlFor={id} className="block text-sm font-medium text-ink mb-1.5">
        {label}
      </label>
      <input
        id={id}
        className="w-full rounded-xl border border-line bg-white/70 px-4 py-2.5 text-[15px] outline-none focus-visible:border-indigo"
        {...props}
      />
      {error && <p className="mt-1.5 text-sm text-terracotta">{error}</p>}
    </div>
  );
}
