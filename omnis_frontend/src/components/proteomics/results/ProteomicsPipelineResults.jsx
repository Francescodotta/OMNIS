import React, { useEffect, useState } from 'react';
import {
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
    Typography, Box, TablePagination, Button, Stack, FormGroup, FormControlLabel, Checkbox
} from '@mui/material';

const ROWS_PER_PAGE = 10;

const COLUMN_CONFIG = [
    { key: "protein_groups", label: "Protein Groups" },
    { key: "gene_name", label: "Gene Name" },
    { key: "organism", label: "Organism" },
    { key: "intensity_default_3", label: "Intensity Default 3" }
];

const ProteinResults = ({ fetchProteinResults }) => {
    const [results, setResults] = useState([]);
    const [page, setPage] = useState(0);
    const [visibleColumns, setVisibleColumns] = useState({
        protein_groups: true,
        gene_name: true,
        organism: true,
        intensity_default_3: true
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchProteinResults();
                setResults(data);
            } catch (error) {
                setResults([]);
            }
        };
        fetchData();
    }, [fetchProteinResults]);

    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    const handleColumnToggle = (key) => {
        setVisibleColumns(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const paginatedResults = results.slice(page * ROWS_PER_PAGE, (page + 1) * ROWS_PER_PAGE);

    return (
        <Box sx={{ width: '100%', maxWidth: '100vw', mx: 'auto', overflowX: 'auto', p: 1 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>Protein Results</Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap' }}>
                <FormGroup row sx={{ ml: 1 }}>
                    {COLUMN_CONFIG.map(col => (
                        <FormControlLabel
                            key={col.key}
                            control={
                                <Checkbox
                                    checked={visibleColumns[col.key]}
                                    onChange={() => handleColumnToggle(col.key)}
                                    color="primary"
                                    size="small"
                                />
                            }
                            label={col.label}
                            sx={{ mr: 1 }}
                        />
                    ))}
                </FormGroup>
            </Stack>
            <TableContainer component={Paper} sx={{ minWidth: 900 }}>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            {visibleColumns.protein_groups && <TableCell sx={{ py: 1 }}>Protein Groups</TableCell>}
                            {visibleColumns.gene_name && <TableCell sx={{ py: 1 }}>Gene Name</TableCell>}
                            {visibleColumns.organism && <TableCell sx={{ py: 1 }}>Organism</TableCell>}
                            {visibleColumns.intensity_default_3 && <TableCell sx={{ py: 1 }}>Intensity Default 3</TableCell>}
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {paginatedResults.map((row, idx) => (
                            <TableRow hover key={idx} sx={{ '& > *': { py: 1 } }}>
                                {visibleColumns.protein_groups && (
                                    <TableCell>{row.protein_groups || <i>n/a</i>}</TableCell>
                                )}
                                {visibleColumns.gene_name && (
                                    <TableCell>{row.gene_name || <i>n/a</i>}</TableCell>
                                )}
                                {visibleColumns.organism && (
                                    <TableCell>{row.organism || <i>n/a</i>}</TableCell>
                                )}
                                {visibleColumns.intensity_default_3 && (
                                    <TableCell>{row.intensity_default_3 ?? <i>n/a</i>}</TableCell>
                                )}
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
                <TablePagination
                    rowsPerPageOptions={[ROWS_PER_PAGE]}
                    component="div"
                    count={results.length}
                    rowsPerPage={ROWS_PER_PAGE}
                    page={page}
                    onPageChange={handleChangePage}
                />
            </TableContainer>
        </Box>
    );
};

export default ProteinResults;