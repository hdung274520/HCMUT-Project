import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";

const plusJakartaSans = Plus_Jakarta_Sans({
  variable: "--font-plus-jakarta-sans",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

export const metadata = {
  title: "Muse 2 EEG & Sinh Hiệu Dashboard",
  description: "Trực quan hóa chỉ số sóng não EEG và sinh hiệu cơ thể của thiết bị Muse 2 headband, tối ưu ngữ cảnh LLM y tế.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="vi" className={`${plusJakartaSans.variable}`}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      </head>
      <body>{children}</body>
    </html>
  );
}
