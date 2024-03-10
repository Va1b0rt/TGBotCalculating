import React from 'react';
import { List,
         Datagrid,
         TextField,
         EditButton,
         TextInput,
         ReferenceInput,
         ArrayField,
         SingleFieldList,
         ChipField, ListGuesser } from "react-admin";

const employerFilters = [
    <TextInput source="name" label="Search" alwaysOn />,
    <TextInput source="name" label="Name" />,
];

import { useQuery } from 'react-query';
import { useDataProvider, Loading, Error } from 'react-admin';

export const EmployerList = () => (
    <List>
        <Datagrid>
            <TextField label="UserID" source="id" />
            <TextField label="Имя" source="name" />
            <TextField label="Код ЕГРПОУ" source="ident_EDRPOU" />
            <TextField label="Адрес" source="residence" />
            <TextField label="Телефон" source="phone" />
            <EditButton />
        </Datagrid>
    </List>
);

export const EmployerEdit = () => (
    <Edit>
        <SimpleForm>
            <TextInput source="id" InputProps={{ disabled: true }} />
            <TextInput label="Имя" source="name" />
            <TextInput label="Код ЕГРПОУ" source="ident_EDRPOU" />
            <TextInput label="Телефон" source="phone" />
            <TextInput label="Адрес" source="residence" multiline rows={5} />
        </SimpleForm>
    </Edit>
);