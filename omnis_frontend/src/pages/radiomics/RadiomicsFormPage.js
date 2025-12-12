import Navbar from "../../components/Navbar";
import RadiomicsForm from "../../components/forms/RadiomicsForm";
import { useParams } from "react-router-dom";

const RadiomicsFormPage = () => {
    const {progressive_id} = useParams();

    return(
        <>
        <RadiomicsForm projectId={progressive_id}/>
        </>
    )
}

export default RadiomicsFormPage