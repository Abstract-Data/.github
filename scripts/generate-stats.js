#!/usr/bin/env node
/**
 * High-tech stats generator scaffold for Abstract Data's organization profile.
 *
 * This script can be extended to fetch live metrics,
 * build custom SVG badges, or update markdown content. It currently logs
 * a structured payload for the GitHub Action to consume.
 */

const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.resolve(__dirname, '..', 'profile');
const OUTPUT_FILE = path.join(OUTPUT_DIR, 'stats.json');
const GITHUB_ORG = process.env.GITHUB_ORG || 'abstract-data';
const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const HEADERS = {
  'Accept': 'application/vnd.github+json',
  ...(GITHUB_TOKEN ? { Authorization: `Bearer ${GITHUB_TOKEN}` } : {})
};

async function fetchJson(url) {
  const response = await fetch(url, { headers: HEADERS });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`Failed request ${url} -> ${response.status}: ${text}`);
  }
  return response.json();
}

async function listOrgRepos() {
  const repos = [];
  let page = 1;
  const perPage = 100;

  while (true) {
    const url = `https://api.github.com/orgs/${GITHUB_ORG}/repos?per_page=${perPage}&page=${page}&type=all&sort=updated`;
    const data = await fetchJson(url);
    if (!Array.isArray(data) || data.length === 0) break;
    repos.push(...data);
    if (data.length < perPage) break;
    page += 1;
  }

  return repos;
}

async function fetchOrgMetrics() {
  try {
    const [org, repos] = await Promise.all([
      fetchJson(`https://api.github.com/orgs/${GITHUB_ORG}`),
      listOrgRepos()
    ]);

    const latestRepo = repos
      .filter(repo => repo.pushed_at)
      .sort((a, b) => new Date(b.pushed_at) - new Date(a.pushed_at))[0];

    const totalStars = repos.reduce((sum, repo) => sum + (repo.stargazers_count || 0), 0);
    const totalForks = repos.reduce((sum, repo) => sum + (repo.forks_count || 0), 0);

    return {
      organization: GITHUB_ORG,
      publicRepos: org.public_repos ?? repos.length,
      privateRepos: org.total_private_repos ?? 0,
      followers: org.followers ?? 0,
      members: org.public_members ?? 0,
      totalStars,
      totalForks,
      latestPushedRepository: latestRepo ? {
        name: latestRepo.name,
        pushedAt: latestRepo.pushed_at,
        htmlUrl: latestRepo.html_url
      } : null
    };
  } catch (error) {
    console.warn(`[WARN] Unable to fetch GitHub metrics: ${error.message}`);
    return {
      organization: GITHUB_ORG,
      publicRepos: 0,
      privateRepos: 0,
      followers: 0,
      members: 0,
      totalStars: 0,
      totalForks: 0,
      latestPushedRepository: null,
      error: error.message
    };
  }
}

async function main() {
  const metrics = await fetchOrgMetrics();

  const payload = {
    generatedAt: new Date().toISOString(),
    systems: [
      { name: 'Quantum Core Labs', status: 'skunkworks', emphasis: '#E7AE59' },
      { name: 'Campaign Intelligence Grid', status: 'operational', emphasis: '#AC2D21' }
    ],
    metrics: {
      repos: metrics.publicRepos + metrics.privateRepos,
      followers: metrics.followers,
      members: metrics.members,
      totalStars: metrics.totalStars,
      totalForks: metrics.totalForks,
      latestCommit: metrics.latestPushedRepository ? metrics.latestPushedRepository.pushedAt : null,
      latestRepository: metrics.latestPushedRepository ? metrics.latestPushedRepository.name : null
    },
    sources: {
      github: `https://github.com/${GITHUB_ORG}`,
      latestRepository: metrics.latestPushedRepository ? metrics.latestPushedRepository.htmlUrl : null
    }
  };

  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  fs.writeFileSync(OUTPUT_FILE, JSON.stringify(payload, null, 2));
  console.log(`Generated stats payload -> ${OUTPUT_FILE}`);
}

main().catch(error => {
  console.error('[ERROR] generate-stats failed:', error);
  process.exit(1);
});
