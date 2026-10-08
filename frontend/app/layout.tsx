import "./globals.css";
import { Providers } from "@/components/providers";
import { Shell } from "@/components/shell";
export const metadata={title:"EvalForge",description:"AI regression and evaluation platform"};
export default function Layout({children}:{children:React.ReactNode}) { return <html lang="en"><body><Providers><Shell>{children}</Shell></Providers></body></html> }
