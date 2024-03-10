import * as React from 'react';
import { useQuery } from 'react-query';
import { useDataProvider, Loading, Error } from 'react-admin';

const UserProfile = () => {
    const dataProvider = useDataProvider();
    const { data, isLoading, error } = useQuery(
        ['employer', 'getOne', { id: 1 }],
        () => dataProvider.getOne('employer', { id: 1 })
    );

    if (isLoading) return <Loading />;
    if (error) return <Error />;
    if (!data) return null;

    return (
        <ul>
            <li>Name: {data.data.name}</li>
            <li>Email: {data.data.email}</li>
        </ul>
    )
};