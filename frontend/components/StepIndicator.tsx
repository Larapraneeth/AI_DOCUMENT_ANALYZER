import { CheckCircle, Loader2 } from "lucide-react";

interface Step {
  id: number;
  label: string;
  icon: React.ElementType;
}

interface Props {
  steps: Step[];
  currentStep: number;
}

export default function StepIndicator({ steps, currentStep }: Props) {
  return (
    <div className="bg-geojit-bg rounded-xl border border-geojit-border p-4">
      <div className="flex items-center justify-between relative">
        {/* Progress line */}
        <div className="absolute top-4 left-0 right-0 h-0.5 bg-geojit-border z-0" />
        <div
          className="absolute top-4 left-0 h-0.5 bg-geojit-blue z-0 transition-all duration-700"
          style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
        />

        {steps.map((step) => {
          const done    = step.id < currentStep;
          const active  = step.id === currentStep;
          const pending = step.id > currentStep;
          const Icon = step.icon;

          return (
            <div key={step.id} className="flex flex-col items-center z-10">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center transition-all
                  ${done   ? "bg-geojit-green text-white" : ""}
                  ${active ? "bg-geojit-blue text-white shadow-lg shadow-blue-200" : ""}
                  ${pending? "bg-white border-2 border-geojit-border text-gray-300" : ""}
                `}
              >
                {done ? (
                  <CheckCircle size={16} />
                ) : active ? (
                  <Loader2 size={16} className="spinner" />
                ) : (
                  <Icon size={14} />
                )}
              </div>
              <span
                className={`text-[10px] mt-1 font-medium max-w-[60px] text-center leading-tight
                  ${done   ? "text-geojit-green" : ""}
                  ${active ? "text-geojit-blue"  : ""}
                  ${pending? "text-gray-400"      : ""}
                `}
              >
                {step.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
