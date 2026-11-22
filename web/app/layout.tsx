import type { Metadata,Viewport } from "next";
import "./globals.css";
export const metadata:Metadata={title:"EcoCycle AI | Circular workspace",description:"Identify materials, estimate recycling impact and find nearby collection centers."};
export const viewport:Viewport={width:"device-width",initialScale:1,themeColor:"#103f36"};
export default function Layout({children}:{children:React.ReactNode}) {return <html lang="en" suppressHydrationWarning><body>{children}</body></html>}
