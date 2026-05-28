import { TopCommandBar } from "@/components/app-shell/top-command-bar";
import { SeedUploadDropzone } from "@/components/imports/seed-upload-dropzone";
import { COPY } from "@/lib/copy";

export const metadata = {
  title: "Imports",
};

export default function ImportsPage() {
  return (
    <>
      <TopCommandBar title={COPY.imports.title} subtitle={COPY.imports.subtitle} />
      <div className="px-6 py-5">
        <div className="mx-auto max-w-3xl">
          <SeedUploadDropzone />
        </div>
      </div>
    </>
  );
}
