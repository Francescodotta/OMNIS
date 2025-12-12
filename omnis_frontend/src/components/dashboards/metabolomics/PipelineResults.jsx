import React, { useEffect, useState } from 'react';
import { fetchMetabolomicsPipelineResults } from "../../../services/metabolomics_api";
import {
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper,
    Typography, Box, IconButton, Collapse, Chip, TablePagination, Button, Stack, FormGroup, FormControlLabel, Checkbox
} from '@mui/material';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

function safeParse(val, fallback = []) {
    if (val == null) return fallback;
    try {
        // Try JSON first
        return JSON.parse(val.replace(/'/g, '"'));
    } catch {
        // Try to parse Python dict-like string: {0: 123, 1: 456}
        try {
            // Add quotes around keys: {0: 123, 1: 456} -> {"0": 123, "1": 456}
            const fixed = val.replace(/([{,]\s*)(\d+)(\s*:)/g, '$1"$2"$3').replace(/'/g, '"');
            return JSON.parse(fixed);
        } catch {
            return fallback;
        }
    }
}

const ROWS_PER_PAGE = 10;

const COLUMN_CONFIG = [
    { key: "hmdb_name", label: "HMDB Name" },
    { key: "hmdb_id", label: "HMDB ID" },
    { key: "kegg_name", label: "KEGG Name" },
    { key: "kegg_id", label: "KEGG ID" },
    { key: "common_annotations", label: "Common Annotations" },
    { key: "mz", label: "m/z" },
    { key: "rt", label: "rt" },
    { key: "peak_area", label: "Peak Area" },
    { key: "precursor_ions", label: "Precursor Ions" },
    { key: "precursor_charges", label: "Precursor Charges" },
    { key: "input_maps", label: "Input Maps" },
    { key: "per_sample_intensity", label: "Per-Sample Intensity" },
    { key: "expand", label: "Expand" }
];

const PipelineResults = ({ projectId, pipelineId }) => {
    const [results, setResults] = useState([]);
    const [openRows, setOpenRows] = useState({});
    const [page, setPage] = useState(0);
    const [showOnlyCommon, setShowOnlyCommon] = useState(false);
    const [visibleColumns, setVisibleColumns] = useState({
        hmdb_name: true,
        hmdb_id: true,
        kegg_name: true,
        kegg_id: true,
        common_annotations: true,
        mz: true,
        rt: true,
        peak_area: true,
        precursor_ions: true,
        precursor_charges: true,
        input_maps: true,
        per_sample_intensity: true,
        expand: true
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                const data = await fetchMetabolomicsPipelineResults(projectId, pipelineId);
                console.log(data)
                const cleaned = data.map(({ ['Unnamed: 0']: _omit, ...rest }) => rest);
                setResults(cleaned);
            } catch (error) {
                setResults([]);
            }
        };
        fetchData();
    }, [projectId, pipelineId]);

    const handleRowClick = (idx) => {
        setOpenRows(prev => ({ ...prev, [idx]: !prev[idx] }));
    };

    const handleChangePage = (event, newPage) => {
        setPage(newPage);
    };

    // Filtering logic for compounds with both HMDB and KEGG matches in common_annotations
    const filteredResults = showOnlyCommon
        ? results.filter(row => {
            const common_annotations = safeParse(row.common_annotations);
            return Array.isArray(common_annotations) && common_annotations.length > 0;
        })
        : results;

    // Pagination logic
    const paginatedResults = filteredResults.slice(page * ROWS_PER_PAGE, (page + 1) * ROWS_PER_PAGE);

    // Column visibility toggle handler
    const handleColumnToggle = (key) => {
        setVisibleColumns(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    return (
        <Box sx={{ width: '100%', maxWidth: '100vw', mx: 'auto', overflowX: 'auto', p: 1 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>Metabolomics Pipeline Results</Typography>
            <Stack direction="row" spacing={1} sx={{ mb: 1, flexWrap: 'wrap' }}>
                <Button
                    variant={showOnlyCommon ? "contained" : "outlined"}
                    color="primary"
                    onClick={() => { setShowOnlyCommon(v => !v); setPage(0); }}
                    size="small"
                >
                    {showOnlyCommon ? "Show All Compounds" : "Show Only HMDB+KEGG Matches"}
                </Button>
                <FormGroup row sx={{ ml: 1 }}>
                    {COLUMN_CONFIG.filter(col => col.key !== "expand").map(col => (
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
            <TableContainer component={Paper} sx={{ minWidth: 1200 }}>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            {visibleColumns.hmdb_name && <TableCell sx={{ py: 1 }}>HMDB Name</TableCell>}
                            {visibleColumns.hmdb_id && <TableCell sx={{ py: 1 }}>HMDB ID</TableCell>}
                            {visibleColumns.kegg_name && <TableCell sx={{ py: 1 }}>KEGG Name</TableCell>}
                            {visibleColumns.kegg_id && <TableCell sx={{ py: 1 }}>KEGG ID</TableCell>}
                            {visibleColumns.common_annotations && <TableCell sx={{ py: 1 }}>Common Annotations</TableCell>}
                            {visibleColumns.mz && <TableCell sx={{ py: 1 }}>m/z</TableCell>}
                            {visibleColumns.rt && <TableCell sx={{ py: 1 }}>rt</TableCell>}
                            {visibleColumns.peak_area && <TableCell sx={{ py: 1 }}>Peak Area</TableCell>}
                            {visibleColumns.precursor_ions && <TableCell sx={{ py: 1 }}>Precursor Ions</TableCell>}
                            {visibleColumns.precursor_charges && <TableCell sx={{ py: 1 }}>Precursor Charges</TableCell>}
                            {visibleColumns.input_maps && <TableCell sx={{ py: 1 }}>Input Maps</TableCell>}
                            {visibleColumns.per_sample_intensity && <TableCell sx={{ py: 1 }}>Per-Sample Intensity</TableCell>}
                            {visibleColumns.expand && <TableCell sx={{ py: 1 }}>Expand</TableCell>}
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {paginatedResults.map((row, idx) => {
                            const globalIdx = page * ROWS_PER_PAGE + idx;
                            const hmdb_matches = safeParse(row.hmdb_matches);
                            const kegg_matches = safeParse(row.kegg_matches);
                            const common_annotations = safeParse(row.common_annotations);

                            const first_hmdb = hmdb_matches[0] || {};
                            const first_kegg = kegg_matches[0] || {};
                            const first_common = common_annotations[0] || {};
                            const first_common_hmdb = first_common.hmdb || {};
                            const first_common_kegg = first_common.kegg || {};

                            const hasMore =
                                hmdb_matches.length > 1 ||
                                kegg_matches.length > 1 ||
                                common_annotations.length > 1;

                            // Always parse these fields, since they are stringified JSON from backend
                            const precursorIons = typeof row.precursor_ions === "string"
                                ? safeParse(row.precursor_ions, [])
                                : row.precursor_ions || [];
                            const precursorCharges = typeof row.precursor_charges === "string"
                                ? safeParse(row.precursor_charges, [])
                                : row.precursor_charges || [];
                            const inputMaps = typeof row.input_maps === "string"
                                ? safeParse(row.input_maps, [])
                                : row.input_maps || [];
                            const perSampleIntensity = typeof row.per_sample_intensity === "string"
                                ? safeParse(row.per_sample_intensity, {})
                                : row.per_sample_intensity || {};

                            return (
                                <React.Fragment key={globalIdx}>
                                    <TableRow hover sx={{ '& > *': { py: 1 } }}>
                                        {visibleColumns.hmdb_name && (
                                            <TableCell>{first_hmdb.name || <i>n/a</i>}</TableCell>
                                        )}
                                        {visibleColumns.hmdb_id && (
                                            <TableCell>
                                                {first_hmdb.accession ? (
                                                    <Chip label={first_hmdb.accession} size="small" color="info" sx={{ my: 0.2 }} />
                                                ) : <i>n/a</i>}
                                            </TableCell>
                                        )}
                                        {visibleColumns.kegg_name && (
                                            <TableCell>{first_kegg.Name || <i>n/a</i>}</TableCell>
                                        )}
                                        {visibleColumns.kegg_id && (
                                            <TableCell>
                                                {first_kegg.KEGG_ID ? (
                                                    <Chip label={first_kegg.KEGG_ID} size="small" color="success" sx={{ my: 0.2 }} />
                                                ) : <i>n/a</i>}
                                            </TableCell>
                                        )}
                                        {visibleColumns.common_annotations && (
                                            <TableCell>
                                                {first_common_hmdb.accession && first_common_kegg.KEGG_ID ? (
                                                    <>
                                                        <Chip label={first_common_hmdb.accession} size="small" color="info" sx={{ mr: 0.5, my: 0.2 }} />
                                                        <Chip label={first_common_kegg.KEGG_ID} size="small" color="success" sx={{ my: 0.2 }} />
                                                    </>
                                                ) : <i>n/a</i>}
                                            </TableCell>
                                        )}
                                        {visibleColumns.mz && (
                                            <TableCell>{row.mz}</TableCell>
                                        )}
                                        {visibleColumns.rt && (
                                            <TableCell>{row.rt}</TableCell>
                                        )}
                                        {visibleColumns.peak_area && (
                                            <TableCell>{row.peak_area ?? <i>n/a</i>}</TableCell>
                                        )}
                                        {visibleColumns.precursor_ions && (
                                            <TableCell>
                                                {precursorIons.length > 0
                                                    ? precursorIons.join(", ")
                                                    : <i>n/a</i>}
                                            </TableCell>
                                        )}
                                        {visibleColumns.precursor_charges && (
                                            <TableCell>
                                                {precursorCharges.length > 0
                                                    ? precursorCharges.join(", ")
                                                    : <i>n/a</i>}
                                            </TableCell>
                                        )}
                                        {visibleColumns.input_maps && (
                                            <TableCell>
                                                {inputMaps.length > 0
                                                    ? inputMaps.join(", ")
                                                    : <i>n/a</i>}
                                            </TableCell>
                                        )}
                                        {visibleColumns.per_sample_intensity && (
                                            <TableCell>
                                                {perSampleIntensity && Object.keys(perSampleIntensity).length > 0 ? (
                                                    <Stack direction="row" spacing={0.5} flexWrap="wrap">
                                                        {Object.entries(perSampleIntensity).map(([sampleIdx, intensity]) => (
                                                            <Chip
                                                                key={sampleIdx}
                                                                label={`S${sampleIdx}: ${Number(intensity).toExponential(2)}`}
                                                                size="small"
                                                                color="secondary"
                                                                sx={{ mb: 0.2 }}
                                                            />
                                                        ))}
                                                    </Stack>
                                                ) : <i>n/a</i>}
                                            </TableCell>
                                        )}
                                        {visibleColumns.expand && (
                                            <TableCell>
                                                {hasMore && (
                                                    <IconButton size="small" onClick={() => handleRowClick(globalIdx)}>
                                                        {openRows[globalIdx] ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
                                                    </IconButton>
                                                )}
                                            </TableCell>
                                        )}
                                    </TableRow>
                                    <TableRow>
                                        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={Object.values(visibleColumns).filter(Boolean).length}>
                                            <Collapse in={openRows[globalIdx]} timeout="auto" unmountOnExit>
                                                <Box margin={1}>
                                                    <Typography variant="subtitle2" sx={{ mb: 0.5 }}>All HMDB Matches:</Typography>
                                                    {hmdb_matches.length > 0 ? (
                                                        hmdb_matches.map((m, i) => (
                                                            <Chip key={i} label={`${m.name} (${m.accession})`} size="small" sx={{ mr: 0.5, mb: 0.5 }} />
                                                        ))
                                                    ) : <Typography variant="body2" color="textSecondary">None</Typography>}
                                                    <Typography variant="subtitle2" sx={{ mt: 1, mb: 0.5 }}>All KEGG Matches:</Typography>
                                                    {kegg_matches.length > 0 ? (
                                                        kegg_matches.map((k, i) => (
                                                            <Chip key={i} label={`${k.Name} (${k.KEGG_ID})`} size="small" color="success" sx={{ mr: 0.5, mb: 0.5 }} />
                                                        ))
                                                    ) : <Typography variant="body2" color="textSecondary">None</Typography>}
                                                    <Typography variant="subtitle2" sx={{ mt: 1, mb: 0.5 }}>All Common Annotations:</Typography>
                                                    {common_annotations.length > 0 ? (
                                                        common_annotations.map((c, i) => (
                                                            <Chip
                                                                key={i}
                                                                label={`HMDB: ${c.hmdb?.accession || ''} / KEGG: ${c.kegg?.KEGG_ID || ''}`}
                                                                size="small"
                                                                color="warning"
                                                                sx={{ mr: 0.5, mb: 0.5 }}
                                                            />
                                                        ))
                                                    ) : <Typography variant="body2" color="textSecondary">None</Typography>}
                                                </Box>
                                            </Collapse>
                                        </TableCell>
                                    </TableRow>
                                </React.Fragment>
                            );
                        })}
                    </TableBody>
                </Table>
                <TablePagination
                    rowsPerPageOptions={[ROWS_PER_PAGE]}
                    component="div"
                    count={filteredResults.length}
                    rowsPerPage={ROWS_PER_PAGE}
                    page={page}
                    onPageChange={handleChangePage}
                />
            </TableContainer>
        </Box>
    );
};

export default PipelineResults;