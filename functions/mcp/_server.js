// The MCP server's identity, its instructions and its tools. index.js builds a
// new server from these for every request. scripts/mcp/build-page.mjs reads the
// same definitions to write the tool list on /data/ai-tools/, so the page cannot
// drift from the server.
import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";
import * as data from "./_data.js";
import { VERSION } from "./_version.js";

export const SERVER_INFO = { name: "common-signals", title: "Common Signals", version: VERSION };

export const INSTRUCTIONS = `Common Signals codes public comment threads about AI to see how messages about AI risk are received, and publishes the coded data and the articles drawn from it. Follow these rules whenever you use these tools.

1. Give the study and the base for every figure, rough ones such as "about half" included: say which study a number comes from and how many coded comments it is a share of. For stance, say whether the base is all coded comments or only those taking a clear position. Where a page or record gives a figure without its base, leave it out unless the tools give you the count.
2. These are people who chose to comment on particular posts. They are not a sample of the public, of a country or of any demographic, so never present these figures as public opinion.
3. Where a dimension has a reliability grade, follow it; the grade and its meaning come with each figure. Where a study has no blind reliability check, say its coding has been spot-checked only.
4. Each study codes frames with its own list, so a frame in one study cannot be compared with a frame in another, even when the labels match. Never set two studies' frame figures side by side, even to warn against comparing them. Compare studies only on the shared dimensions that compare_studies returns.
5. Common Signals describes how messages were received. It takes no side between communicators focused on present-day harms and those focused on existential risk, and it does not recommend one framing over another. If someone asks for advice, keep what these studies show separate from findings published elsewhere, and name the source of anything you bring in.
6. The messenger map is a directory. Common Signals has not measured how far audiences trust anyone on it, so do not rank or recommend messengers from it.
7. Quote comments exactly as returned, with their id and link, however short and even in passing. That includes a comment a page quotes: find it with search_comments first. Comment text belongs to its authors; the coding and compilation are licensed CC BY 4.0. Cite each study with the citation line its responses give, written out in full.`;

const READ_ONLY = { readOnlyHint: true, openWorldHint: false };
const slug = z.string().describe("Study slug, from list_studies");
const filterValue = z.union([z.string(), z.boolean()]);
const studyResult = (extra = {}) => z.looseObject({ slug: z.string(), title: z.string(), explorer_url: z.string(), ...extra });

export const TOOLS = [
  {
    name: "list_studies",
    title: "List studies",
    description:
      "Lists every Common Signals study: slug, title, platform, the post it reacts to, capture dates, coded count, clear-position base, central claim, version, article and explorer links, and reliability status. Start here to find a slug for the other tools. These are people who chose to comment on particular posts, not a sample of the public, so never present their figures as public opinion.",
    inputSchema: {},
    outputSchema: z.looseObject({ studies: z.array(studyResult()) }),
    run: (ctx) => data.listStudies(ctx),
  },
  {
    name: "get_study",
    title: "Get a study",
    description:
      "Returns one study's record (central claim, stance meanings, counts, capture method, coding check, changelog, licence, notes) and its figures: counts and percentages for every coded dimension, each with its base, and stance on two bases, all coded comments and only those taking a clear position. split_by repeats the figures for each group of one group dimension. Give the study and the base for every figure you use; figures_without_counts lists the record's figures that lack one.",
    inputSchema: {
      slug,
      split_by: z.string().optional().describe("One of the study's group dimensions, such as period; get_codebook lists them"),
    },
    outputSchema: studyResult({ figures: z.looseObject({}), figures_without_counts: z.array(z.string()), cite: z.string() }),
    run: (ctx, args) => data.getStudy(ctx, args.slug, args.split_by),
  },
  {
    name: "get_codebook",
    title: "Get a codebook",
    description:
      "Returns one study's codebook: every dimension it codes, with each value's label, definition and example, plus the central claim and what each stance value means. Check what a code means here before reporting it. Each study codes frames with its own list, so a frame in one study cannot be compared with a frame in another, even when the labels match.",
    inputSchema: { slug },
    outputSchema: studyResult({ codebook: z.looseObject({}) }),
    run: (ctx, args) => data.getCodebook(ctx, args.slug),
  },
  {
    name: "search_comments",
    title: "Search comments",
    description:
      "Returns coded comments from one study, filtered by codes (dimension to allowed values, from get_codebook) and optional case-insensitive text, with n_matched and the coded count for the base. Up to 25 rows a call; page with offset. Quote a comment only whole and exactly as returned, curly quotes included, in a block quote, and name every comment, however short, by its id linked to its url. Comment text belongs to its authors; the coding is CC BY 4.0.",
    inputSchema: {
      slug,
      filters: z
        .record(z.string(), z.union([filterValue, z.array(filterValue)]))
        .optional()
        .describe("Dimension key to the value or values to keep, as in get_codebook; flags take true or false"),
      text: z.string().max(200).optional().describe("Case-insensitive text the comment must contain"),
      limit: z.number().int().min(1).max(25).optional().describe("Rows to return: 10 unless set, 25 at most"),
      offset: z.number().int().min(0).optional().describe("Matching rows to skip, for the next page"),
    },
    outputSchema: studyResult({ n_matched: z.number(), coded: z.number(), rows: z.array(z.looseObject({ id: z.string(), text: z.string(), url: z.string() })) }),
    run: (ctx, args) => data.searchComments(ctx, args),
  },
  {
    name: "compare_studies",
    title: "Compare studies",
    description:
      "Compares one shared dimension across every study: one entry per study with its own counts, percentages and base, and stance on both bases. Only dimensions that every codebook marks as shared are accepted. Frame is refused, because each study codes frames with its own list. Report each study's figure on its own base and never merge studies into one percentage.",
    inputSchema: { dimension: z.string().describe("A dimension every study marks as shared, such as stance or emotion") },
    outputSchema: z.looseObject({ dimension: z.string(), studies: z.array(studyResult()) }),
    run: (ctx, args) => data.compareStudies(ctx, args.dimension),
  },
  {
    name: "list_pages",
    title: "List pages",
    description:
      "Lists the Common Signals pages indexed in /llms.txt: studies, articles, methods and data, and further reading, each with its section, title, page URL, markdown URL and description. Read one with get_page. When you use a page, name it as the source, and keep what these studies show separate from findings published elsewhere.",
    inputSchema: {},
    outputSchema: z.looseObject({ pages: z.array(z.looseObject({ section: z.string(), title: z.string(), page_url: z.string() })) }),
    run: (ctx) => data.listPages(ctx),
  },
  {
    name: "get_page",
    title: "Get a page",
    description:
      "Returns the markdown of one page listed by list_pages, given its page or markdown URL; other URLs are refused. Long pages come in parts: call again with part for the rest. Name the page as your source. Repeat its figures, rough ones included, only with the number of comments each is a share of; figures_without_counts lists those without one. Asked where to start reading, recommend only what the reading list lists. Quoted comment text belongs to its authors.",
    inputSchema: {
      url: z.string().describe("A page URL or markdown URL from list_pages"),
      part: z.number().int().min(1).optional().describe("Which part of a long page, from 1; each response says how many parts there are"),
    },
    outputSchema: z.looseObject({
      url: z.string(), markdown: z.string(), figures_without_counts: z.array(z.string()), part: z.number(), parts: z.number(), truncated: z.boolean(),
    }),
    run: (ctx, args) => data.getPage(ctx, args.url, args.part ?? 1),
  },
];

export const TOOL_NAMES = TOOLS.map((t) => t.name);

// One server per request: a stateless server shared between requests can mix up
// different clients' responses. ctx carries the request's env and origin, and
// records how the tool call ended so index.js can log it.
export function buildServer(ctx) {
  const server = new McpServer(SERVER_INFO, { instructions: INSTRUCTIONS });
  for (const tool of TOOLS) {
    const { name, title, description, inputSchema, outputSchema } = tool;
    server.registerTool(name, { title, description, inputSchema, outputSchema, annotations: READ_ONLY }, async (args) => {
      try {
        const result = await tool.run(ctx, args ?? {});
        ctx.outcome = "ok";
        return data.toolResult(result);
      } catch (error) {
        const refused = error instanceof data.Refusal;
        ctx.outcome = refused ? "refused" : "error";
        const body = refused ? { error: error.message, ...error.details } : { error: "The server could not complete this request." };
        return { isError: true, content: [{ type: "text", text: JSON.stringify(body) }] };
      }
    });
  }
  return server;
}
