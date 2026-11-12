/**
 * People shown on /team. Intentionally empty: add real team members here
 * (name, role, optional one-line bio). The page shows a labelled "Example"
 * placeholder until at least one real entry exists.
 */
export type TeamMember = {
  name: string;
  role: string;
  bio?: string;
};

export const teamMembers: TeamMember[] = [];
