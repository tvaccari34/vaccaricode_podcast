// UI strings + routing helpers for the bilingual site.
// Primary language (pt-BR) lives at the site root; secondary (en) lives under /en.

export const LANGS = ["pt-BR", "en"];

export const STRINGS = {
  "pt-BR": {
    htmlLang: "pt-BR",
    base: "", // URL prefix for this language
    other: "en",
    otherLabel: "EN",
    selfLabel: "PT",
    tagline: "tendências em TI e dev",
    nav: { blog: "Blog", podcast: "Podcast", about: "Sobre", subscribe: "Assinar" },
    heroTitle: "Tendências em software e IA, no piloto automático",
    heroBody:
      "Um blog, newsletter e podcast automatizados cobrindo o que está em movimento em TI e desenvolvimento de software — escritos e narrados a partir de fontes reais. Por",
    latestPosts: "Últimos posts",
    episodes: "Episódios do podcast",
    archive: "Arquivo",
    months: ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
             "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"],
    noPosts: "Nenhum post publicado ainda.",
    noEpisodes: "Nenhum episódio publicado ainda.",
    audioSoon: "áudio em breve",
    showNotes: "Notas do episódio",
    allPosts: "← todos os posts",
    listenEpisode: "ouça o episódio →",
    allEpisodes: "← todos os episódios",
    readPost: "leia o post →",
    podcastIntro: "Cada episódio é narrado a partir das mesmas fontes do post correspondente.",
    footer: "tendências em software e IA, automatizadas",
    rssLabel: "RSS",
    feedLabel: "Feed do podcast",
  },
  en: {
    htmlLang: "en",
    base: "/en",
    other: "pt-BR",
    otherLabel: "PT",
    selfLabel: "EN",
    tagline: "IT & dev trends",
    nav: { blog: "Blog", podcast: "Podcast", about: "About", subscribe: "Subscribe" },
    heroTitle: "Trends in software & AI, on autopilot",
    heroBody:
      "An automated blog, newsletter, and podcast covering what's moving in IT and software development — written and narrated from real sources. By",
    latestPosts: "Latest posts",
    episodes: "Podcast episodes",
    archive: "Archive",
    months: ["January", "February", "March", "April", "May", "June",
             "July", "August", "September", "October", "November", "December"],
    noPosts: "No published posts yet.",
    noEpisodes: "No published episodes yet.",
    audioSoon: "audio coming soon",
    showNotes: "Show notes",
    allPosts: "← all posts",
    listenEpisode: "listen to the episode →",
    allEpisodes: "← all episodes",
    readPost: "read the post →",
    podcastIntro: "Each episode is narrated from the same sources as the matching blog post.",
    footer: "automated trends in software & AI",
    rssLabel: "RSS",
    feedLabel: "Podcast feed",
  },
};

/** Prefix a path for a language: pt-BR → "/blog", en → "/en/blog". */
export function href(lang, path) {
  return (STRINGS[lang].base + path) || "/";
}
