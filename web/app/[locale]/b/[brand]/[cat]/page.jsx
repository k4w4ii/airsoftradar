import { CollectionPage, collectionMetadata } from "../../../../../components/Collection";

export async function generateMetadata({ params }) {
  return collectionMetadata(await params);
}

export default async function Page({ params, searchParams }) {
  return <CollectionPage {...(await params)} sp={await searchParams} />;
}
