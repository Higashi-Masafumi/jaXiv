import type { Route } from "./+types/home";
import { Welcome } from "~/welcome/welcome";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "arXiv Translator" },
    {
      name: "description",
      content: "Translate arXiv papers with live progress",
    },
  ];
}

export default function Home() {
  return <Welcome />;
}
