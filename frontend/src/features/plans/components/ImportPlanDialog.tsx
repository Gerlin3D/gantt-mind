import { type FormEvent, useEffect, useRef, useState } from 'react';
import { getSampleWorkbookUrl } from '../api/plansApi';
import type { ImportValidationErrorPayload } from '../model/types';

type ImportPlanDialogProps = {
  isOpen: boolean;
  isImporting: boolean;
  validationError: ImportValidationErrorPayload | null;
  genericError: string | null;
  onClose: () => void;
  onImport: (request: { file: File; planName: string; startDate: string }) => Promise<void>;
};

export function ImportPlanDialog({
  isOpen,
  isImporting,
  validationError,
  genericError,
  onClose,
  onImport,
}: ImportPlanDialogProps) {
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [planName, setPlanName] = useState('Imported plan');
  const [startDate, setStartDate] = useState('2026-01-05');
  const [localError, setLocalError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    closeButtonRef.current?.focus();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape' && !isImporting) {
        onClose();
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isImporting, isOpen, onClose]);

  if (!isOpen) {
    return null;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLocalError(null);

    if (!file) {
      setLocalError('Choose an .xlsx file.');
      return;
    }
    if (!planName.trim()) {
      setLocalError('Plan name is required.');
      return;
    }
    if (!startDate) {
      setLocalError('Start date is required.');
      return;
    }

    await onImport({ file, planName, startDate });
  }

  return (
    <div className="drawer-backdrop" role="presentation" onMouseDown={isImporting ? undefined : onClose}>
      <section
        className="import-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="import-dialog-title"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <header className="drawer-header">
          <div>
            <p className="eyebrow">Excel import</p>
            <h2 id="import-dialog-title">Import Excel</h2>
          </div>
          <button
            ref={closeButtonRef}
            className="icon-button"
            type="button"
            onClick={onClose}
            disabled={isImporting}
            aria-label="Close import dialog"
          >
            X
          </button>
        </header>
        <form className="import-form" onSubmit={(event) => void handleSubmit(event)}>
          <label>
            <span>Workbook</span>
            <input
              type="file"
              accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              onChange={(event) => setFile(event.currentTarget.files?.[0] ?? null)}
              disabled={isImporting}
            />
          </label>
          {file ? <p className="selected-file">{file.name}</p> : null}
          <label>
            <span>Plan name</span>
            <input
              value={planName}
              onChange={(event) => setPlanName(event.currentTarget.value)}
              disabled={isImporting}
            />
          </label>
          <label>
            <span>Start date</span>
            <input
              type="date"
              value={startDate}
              onChange={(event) => setStartDate(event.currentTarget.value)}
              disabled={isImporting}
            />
          </label>
          <a className="sample-link" href={getSampleWorkbookUrl()} download>
            Download sample workbook
          </a>
          {localError ? <p className="form-error">{localError}</p> : null}
          {genericError ? <p className="form-error">{genericError}</p> : null}
          {validationError ? (
            <div className="validation-report" role="alert">
              <p>{validationError.message}</p>
              <ul>
                {validationError.errors.map((error, index) => (
                  <li key={`${error.code}-${error.row ?? 'file'}-${index}`}>
                    <strong>{error.code}</strong>
                    {error.row ? ` row ${error.row}` : ''}
                    {error.column ? `, ${error.column}` : ''}: {error.message}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
          <div className="dialog-actions">
            <button className="secondary-button" type="button" onClick={onClose} disabled={isImporting}>
              Cancel
            </button>
            <button className="primary-button" type="submit" disabled={isImporting}>
              {isImporting ? 'Importing' : 'Import'}
            </button>
          </div>
        </form>
      </section>
    </div>
  );
}
