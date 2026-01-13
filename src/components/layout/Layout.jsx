import React from "react";
import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Footer from "./Footer";
import ChatLauncher from "../chat/ChatLauncher";

export default function Layout() {
  return (
    <>
      <Navbar />
      <main className="container">
        <Outlet />
      </main>

      <ChatLauncher />
      <Footer />
    </>
  );
}
