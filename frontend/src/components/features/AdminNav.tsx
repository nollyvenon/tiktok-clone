'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const TABS = [
  { href: '/admin', label: 'Overview' },
  { href: '/admin/users', label: 'Users' },
  { href: '/admin/moderation', label: 'Reports' },
  { href: '/admin/audit-log', label: 'Audit Log' },
];

export default function AdminNav() {
  const pathname = usePathname();

  return (
    <div className="flex gap-6 mb-8 border-b border-gray-200 dark:border-gray-800">
      {TABS.map((tab) => (
        <Link
          key={tab.href}
          href={tab.href}
          className={`pb-3 text-sm font-semibold border-b-2 transition ${
            pathname === tab.href
              ? 'border-pink-600 text-pink-600'
              : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-gray-200'
          }`}
        >
          {tab.label}
        </Link>
      ))}
    </div>
  );
}
