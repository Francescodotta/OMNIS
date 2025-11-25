import api from '../utils/ApiMetabolomics';
import authApi from '../utils/Api'; // Add auth API import

// ========== FIELD ASSIGNMENT OPERATIONS ==========

export const assignStandardizedFields = async (projectId, experimentId, fieldAssignments) => {
    try {
        console.log('API Call - assignStandardizedFields:', {
            projectId,
            experimentId,
            fieldAssignments,
            url: `/api/v1/project/${projectId}/experiments/${experimentId}/standardized_fields`
        });

        const response = await api.post(
            `/api/v1/project/${projectId}/experiments/${experimentId}/standardized_fields`,
            { field_assignments: fieldAssignments }
        );
        
        console.log('API Response - assignStandardizedFields:', response.data);
        return response.data;
    } catch (error) {
        console.error('API Error - assignStandardizedFields:', error);
        console.error('Error response:', error.response?.data);
        console.error('Error status:', error.response?.status);
        throw new Error(error.response?.data?.error || 'Error assigning standardized fields');
    }
};

export const updateSingleStandardizedField = async (projectId, experimentId, fieldName, fieldValue) => {
    try {
        const response = await api.put(
            `/api/v1/project/${projectId}/experiments/${experimentId}/standardized_fields/${fieldName}`,
            { field_value: fieldValue }
        );
        return response.data;
    } catch (error) {
        console.error('Error updating standardized field:', error);
        throw new Error(error.response?.data?.error || 'Error updating standardized field');
    }
};

export const removeStandardizedField = async (projectId, experimentId, fieldName) => {
    try {
        const response = await api.delete(
            `/api/v1/project/${projectId}/experiments/${experimentId}/standardized_fields/${fieldName}`
        );
        return response.data;
    } catch (error) {
        console.error('Error removing standardized field:', error);
        throw new Error(error.response?.data?.error || 'Error removing standardized field');
    }
};

// ========== BULK OPERATIONS ==========

export const bulkAssignStandardizedFields = async (projectId, assignments) => {
    try {
        const response = await api.post(
            `/api/v1/project/${projectId}/experiments/standardized_fields/bulk_assign`,
            { assignments }
        );
        return response.data;
    } catch (error) {
        console.error('Error bulk assigning standardized fields:', error);
        throw new Error(error.response?.data?.error || 'Error bulk assigning standardized fields');
    }
};

// ========== QUERY AND ANALYTICS ==========

export const getExperimentsWithStandardizedFields = async (projectId) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/experiments/standardized_fields`);
        return response.data;
    } catch (error) {
        console.error('Error fetching experiments with standardized fields:', error);
        throw new Error('Error fetching experiments with standardized fields');
    }
};

export const findExperimentsByFieldValue = async (projectId, fieldName, fieldValue) => {
    try {
        const response = await api.get(
            `/api/v1/project/${projectId}/standardized_fields/${fieldName}/experiments?field_value=${fieldValue}`
        );
        return response.data;
    } catch (error) {
        console.error('Error finding experiments by field value:', error);
        throw new Error('Error finding experiments by field value');
    }
};

export const getFieldValueDistribution = async (projectId, fieldName) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/standardized_fields/${fieldName}/distribution`);
        return response.data;
    } catch (error) {
        console.error('Error getting field value distribution:', error);
        throw new Error('Error getting field value distribution');
    }
};

export const getStandardizedFieldsSummary = async (projectId) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/standardized_fields/summary`);
        return response.data;
    } catch (error) {
        console.error('Error getting standardized fields summary:', error);
        throw new Error('Error getting standardized fields summary');
    }
};

// ========== COMPLIANCE AND VALIDATION ==========

export const getExperimentsMissingRequiredFields = async (projectId) => {
    try {
        const response = await api.get(`/api/v1/project/${projectId}/experiments/missing_required_fields`);
        return response.data;
    } catch (error) {
        console.error('Error getting experiments missing required fields:', error);
        throw new Error('Error getting experiments missing required fields');
    }
};

export const validateFieldAssignment = async (projectId, fieldName, fieldValue) => {
    try {
        console.log('API Call - validateFieldAssignment:', {
            projectId,
            fieldName,
            fieldValue
        });

        const response = await api.post(
            `/api/v1/project/${projectId}/standardized_fields/validate`,
            { field_name: fieldName, field_value: fieldValue }
        );
        
        console.log('API Response - validateFieldAssignment:', response.data);
        return response.data;
    } catch (error) {
        console.error('API Error - validateFieldAssignment:', error);
        console.error('Error response:', error.response?.data);
        
        // Return a default valid response if validation endpoint doesn't exist
        if (error.response?.status === 404) {
            return { is_valid: true, message: "Valid" };
        }
        
        throw new Error('Error validating field assignment');
    }
};

// ========== FIELD DEFINITIONS ==========

export const getProjectStandardizedFields = async (projectId, fieldType = null) => {
    try {
        console.log('=== Fetching Project Standardized Fields ===');
        console.log('Project ID:', projectId);
        console.log('Field Type Filter:', fieldType);
        
        // Call the auth microservice to get standardized fields for the project
        const url = fieldType 
            ? `/api/projects/${projectId}/standardized-fields?field_type=${fieldType}`
            : `/api/projects/${projectId}/standardized-fields`;
        
        console.log('Auth API URL:', url);
        
        const response = await authApi.get(url);
        console.log('Auth API Response:', response.data);
        
        // Transform the response to match expected format
        const standardizedFields = response.data || [];
        
        console.log('Standardized fields from auth service:', standardizedFields);
        
        return {
            project_id: projectId,
            standardized_fields: standardizedFields,
            total_count: standardizedFields.length,
            success: true
        };
        
    } catch (error) {
        console.error('Error fetching standardized fields from auth service:', error);
        console.error('Error response:', error.response?.data);
        console.error('Error status:', error.response?.status);
        
        // If no fields found, return empty array instead of throwing error
        if (error.response?.status === 404 || error.response?.status === 400) {
            console.log('No standardized fields found for project, returning empty array');
            return {
                project_id: projectId,
                standardized_fields: [],
                total_count: 0,
                success: true,
                message: 'No standardized fields found for this project'
            };
        }
        
        throw new Error('Error getting project standardized fields: ' + (error.response?.data?.error || error.message));
    }
};

export const getStandardizedFieldByName = async (projectId, fieldName) => {
    try {
        const response = await authApi.get(`/api/projects/${projectId}/standardized-fields/${fieldName}`);
        return response.data;
    } catch (error) {
        console.error('Error getting standardized field by name:', error);
        throw new Error('Error getting standardized field by name');
    }
};

export const getRequiredFields = async (projectId) => {
    try {
        // Get all fields and filter required ones
        const fieldsResponse = await getProjectStandardizedFields(projectId);
        const requiredFields = fieldsResponse.standardized_fields.filter(field => field.is_required);
        
        return {
            project_id: projectId,
            required_fields: requiredFields,
            total_count: requiredFields.length
        };
    } catch (error) {
        console.error('Error getting required fields:', error);
        throw new Error('Error getting required fields');
    }
};

// ========== FIELD ASSIGNMENT OPERATIONS (to metabolomics service) ==========