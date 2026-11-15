import { Icon } from "../components/icons";
import { ButtonLink, PageHeader } from "../components/ui";

export default function NotFound() {
  return (
    <div className="py-10">
      <PageHeader eyebrow="404" title="This page does not exist" lede="The investigation you were following is still here. Return to the Observatory or pick a view from the navigation." />
      <ButtonLink to="/" variant="primary" icon={<Icon.Overview size={16} />}>Back to the Observatory</ButtonLink>
    </div>
  );
}
