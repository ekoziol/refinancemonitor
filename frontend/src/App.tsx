import { InputForm } from './components';
import type { CalculatorFormData } from './types/forms';

function App() {
  const handleSubmit = (data: CalculatorFormData) => {
    console.log('Form submitted:', data);
    // TODO: Send to API
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <h1 className="text-3xl font-bold text-gray-900 text-center mb-8">
          Refinance Calculator
        </h1>
        <InputForm onSubmit={handleSubmit} />
      </div>
    </div>
  );
}

export default App;
